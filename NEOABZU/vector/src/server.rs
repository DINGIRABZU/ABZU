use std::io::ErrorKind;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::{Arc, RwLock};
use std::time::Instant;

#[cfg(feature = "tracing")]
use tracing::{info, instrument, warn};

use crate::proto::vector_service_server::{VectorService, VectorServiceServer};
use crate::proto::{InitRequest, InitResponse, SearchRequest, SearchResponse, SearchResult};
use metrics::{counter, gauge, histogram};
use serde::{Deserialize, Serialize};
use sled::Tree;
use thiserror::Error;
use tonic::{transport::Server, Request, Response, Status};

fn embed(text: &str) -> Vec<f32> {
    text.bytes().map(|b| b as f32 / 255.0).collect()
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let mag_a = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let mag_b = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    dot / (mag_a * mag_b + f32::EPSILON)
}

type Shard = Arc<RwLock<Vec<(String, Vec<f32>)>>>;

#[derive(Debug, Error)]
enum VectorError {
    #[error("configuration error: {0}")]
    Config(String),
    #[error("persistent store is empty")]
    EmptyStore,
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("storage error: {0}")]
    Storage(#[from] sled::Error),
}

impl VectorError {
    fn into_status(self) -> Status {
        match self {
            VectorError::Config(msg) => Status::invalid_argument(msg),
            VectorError::EmptyStore => Status::failed_precondition("vector store is empty"),
            VectorError::Io(err) => Status::internal(err.to_string()),
            VectorError::Serialization(err) => Status::internal(err.to_string()),
            VectorError::Storage(err) => Status::internal(err.to_string()),
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct StoredRecord {
    text: String,
    embedding: Vec<f32>,
}

#[derive(Debug)]
struct PersistentStorage {
    db: sled::Db,
}

impl PersistentStorage {
    fn open(path: PathBuf) -> Result<Self, VectorError> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent)?;
            }
        }
        let db = sled::Config::new().path(path).open()?;
        Ok(Self { db })
    }

    fn entries(&self) -> Result<Tree, VectorError> {
        Ok(self.db.open_tree("entries")?)
    }

    fn replace(&self, records: &[StoredRecord]) -> Result<(), VectorError> {
        let tree = self.entries()?;
        tree.clear()?;
        for (idx, record) in records.iter().enumerate() {
            let key = (idx as u64).to_be_bytes();
            let value = serde_json::to_vec(record)?;
            tree.insert(key, value)?;
        }
        tree.flush()?;
        self.db.flush()?;
        Ok(())
    }

    fn load(&self) -> Result<Vec<StoredRecord>, VectorError> {
        let tree = self.entries()?;
        let mut records = Vec::new();
        for item in tree.iter() {
            let (_, value) = item?;
            let record: StoredRecord = serde_json::from_slice(&value)?;
            records.push(record);
        }
        Ok(records)
    }
}

#[derive(Clone)]
pub struct VectorServer {
    shards: Vec<Shard>,
    storage: Arc<PersistentStorage>,
}

impl VectorServer {
    fn new() -> Result<Self, VectorError> {
        let shard_count = std::env::var("NEOABZU_VECTOR_SHARDS")
            .ok()
            .and_then(|s| s.parse::<usize>().ok())
            .filter(|n| *n > 0)
            .unwrap_or(1);

        let db_path = std::env::var("NEOABZU_VECTOR_DB")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from("neoabzu-vector.db"));

        if db_path.as_os_str().is_empty() {
            return Err(VectorError::Config(
                "NEOABZU_VECTOR_DB must not be empty".to_string(),
            ));
        }

        let storage = PersistentStorage::open(db_path)?;
        let shards = (0..shard_count)
            .map(|_| Arc::new(RwLock::new(Vec::new())))
            .collect();
        Ok(Self {
            shards,
            storage: Arc::new(storage),
        })
    }

    fn load_store(&self, records: &[StoredRecord]) {
        let shard_count = self.shards.len().max(1);
        let mut partitioned: Vec<Vec<(String, Vec<f32>)>> = vec![Vec::new(); shard_count];
        for (i, record) in records.iter().enumerate() {
            let idx = i % shard_count;
            partitioned[idx].push((record.text.clone(), record.embedding.clone()));
        }

        for (shard, entries) in self.shards.iter().zip(partitioned.into_iter()) {
            let mut store = shard.write().unwrap();
            *store = entries;
        }
        gauge!("neoabzu_vector_store_size", records.len() as f64);
    }

    fn load_from_persistence(&self) -> Result<Vec<StoredRecord>, VectorError> {
        let records = self.storage.load()?;
        if records.is_empty() {
            Err(VectorError::EmptyStore)
        } else {
            Ok(records)
        }
    }

    fn ensure_loaded(&self) -> Result<(), VectorError> {
        let all_empty = self
            .shards
            .iter()
            .all(|shard| shard.read().unwrap().is_empty());
        if all_empty {
            let records = self.load_from_persistence()?;
            self.load_store(&records);
        }
        Ok(())
    }
}

#[tonic::async_trait]
impl VectorService for VectorServer {
    #[cfg_attr(feature = "tracing", instrument(skip(self)))]
    async fn init(&self, _request: Request<InitRequest>) -> Result<Response<InitResponse>, Status> {
        counter!("neoabzu_vector_init_total", 1);
        let start = Instant::now();
        let maybe_path = match std::env::var("NEOABZU_VECTOR_STORE") {
            Ok(path) => Some(PathBuf::from(path)),
            Err(std::env::VarError::NotPresent) => None,
            Err(err) => {
                return Err(
                    VectorError::Config(format!("invalid NEOABZU_VECTOR_STORE: {err}"))
                        .into_status(),
                )
            }
        };

        let records = if let Some(path) = maybe_path {
            #[cfg(feature = "tracing")]
            info!(store = %path.display(), "loading vector store from dataset");
            match std::fs::read_to_string(&path) {
                Ok(data) => {
                    let texts: Vec<String> = serde_json::from_str(&data)
                        .map_err(|err| VectorError::Serialization(err).into_status())?;
                    if texts.is_empty() {
                        return Err(Status::failed_precondition("vector store dataset is empty"));
                    }
                    let records: Vec<StoredRecord> = texts
                        .into_iter()
                        .map(|text| StoredRecord {
                            embedding: embed(&text),
                            text,
                        })
                        .collect();
                    self.storage
                        .replace(&records)
                        .map_err(VectorError::into_status)?;
                    records
                }
                Err(err) if err.kind() == ErrorKind::NotFound => {
                    #[cfg(feature = "tracing")]
                    warn!(store = %path.display(), "dataset missing, falling back to persistent store");
                    self.load_from_persistence()
                        .map_err(VectorError::into_status)?
                }
                Err(err) => return Err(VectorError::Io(err).into_status()),
            }
        } else {
            #[cfg(feature = "tracing")]
            info!("loading vector store from persistence");
            self.load_from_persistence()
                .map_err(VectorError::into_status)?
        };

        let count = records.len();
        if count == 0 {
            return Err(Status::failed_precondition("vector store is empty"));
        }

        self.load_store(&records);
        histogram!(
            "neoabzu_vector_init_latency_seconds",
            start.elapsed().as_secs_f64()
        );
        #[cfg(feature = "tracing")]
        info!(count, "store initialized");
        Ok(Response::new(InitResponse {
            message: format!("loaded {count}"),
        }))
    }

    #[cfg_attr(feature = "tracing", instrument(skip(self)))]
    async fn search(
        &self,
        request: Request<SearchRequest>,
    ) -> Result<Response<SearchResponse>, Status> {
        counter!("neoabzu_vector_search_total", 1);
        let start = Instant::now();
        let req = request.into_inner();
        if req.top_n == 0 {
            return Err(Status::invalid_argument("top_n must be > 0"));
        }

        if let Err(err) = self.ensure_loaded() {
            return Err(match err {
                VectorError::EmptyStore => Status::failed_precondition("store not initialized"),
                other => other.into_status(),
            });
        }
        #[cfg(feature = "tracing")]
        info!(top_n = req.top_n, text = %req.text, "search request");
        let query_emb = embed(&req.text);
        let mut results: Vec<SearchResult> = Vec::new();
        for shard in &self.shards {
            let store = shard.read().unwrap();
            results.extend(store.iter().map(|(text, emb)| SearchResult {
                text: text.clone(),
                score: cosine_similarity(&query_emb, emb),
                embedding: emb.clone(),
            }));
        }
        results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
        let top = results.into_iter().take(req.top_n as usize).collect();
        histogram!(
            "neoabzu_vector_search_latency_seconds",
            start.elapsed().as_secs_f64()
        );
        Ok(Response::new(SearchResponse { results: top }))
    }
}

#[cfg_attr(feature = "tracing", instrument)]
pub async fn serve(addr: SocketAddr) -> Result<(), Box<dyn std::error::Error>> {
    #[cfg(feature = "tracing")]
    info!(?addr, "starting vector server");
    let server =
        VectorServer::new().map_err(|err| -> Box<dyn std::error::Error> { Box::new(err) })?;
    Server::builder()
        .add_service(VectorServiceServer::new(server))
        .serve(addr)
        .await?;
    Ok(())
}
