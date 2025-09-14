use std::net::SocketAddr;
use std::sync::{Arc, RwLock};

use crate::proto::vector_service_server::{VectorService, VectorServiceServer};
use crate::proto::{InitRequest, InitResponse, SearchRequest, SearchResponse, SearchResult};
use metrics::{counter, gauge};
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

#[derive(Clone)]
pub struct VectorServer {
    shards: Vec<Arc<RwLock<Vec<(String, Vec<f32>)>>>>,
}

impl Default for VectorServer {
    fn default() -> Self {
        let shard_count = std::env::var("NEOABZU_VECTOR_SHARDS")
            .ok()
            .and_then(|s| s.parse::<usize>().ok())
            .filter(|n| *n > 0)
            .unwrap_or(1);
        let shards = (0..shard_count)
            .map(|_| Arc::new(RwLock::new(Vec::new())))
            .collect();
        Self { shards }
    }
}

impl VectorServer {
    fn load_store(&self, texts: Vec<String>) {
        for (i, t) in texts.into_iter().enumerate() {
            let shard = &self.shards[i % self.shards.len()];
            let mut store = shard.write().unwrap();
            store.push((t.clone(), embed(&t)));
        }
        let total: usize = self.shards.iter().map(|s| s.read().unwrap().len()).sum();
        gauge!("neoabzu_vector_store_size", total as f64);
    }
}

#[tonic::async_trait]
impl VectorService for VectorServer {
    async fn init(&self, _request: Request<InitRequest>) -> Result<Response<InitResponse>, Status> {
        counter!("neoabzu_vector_init_total", 1);
        let path = std::env::var("NEOABZU_VECTOR_STORE")
            .map_err(|_| Status::invalid_argument("NEOABZU_VECTOR_STORE not set"))?;
        let data = std::fs::read_to_string(&path)
            .map_err(|e| Status::internal(format!("failed to read store: {e}")))?;
        let texts: Vec<String> = serde_json::from_str(&data)
            .map_err(|e| Status::internal(format!("invalid store: {e}")))?;
        self.load_store(texts);
        let count: usize = self.shards.iter().map(|s| s.read().unwrap().len()).sum();
        Ok(Response::new(InitResponse {
            message: format!("loaded {count}"),
        }))
    }

    async fn search(
        &self,
        request: Request<SearchRequest>,
    ) -> Result<Response<SearchResponse>, Status> {
        counter!("neoabzu_vector_search_total", 1);
        let req = request.into_inner();
        if req.top_n == 0 {
            return Err(Status::invalid_argument("top_n must be > 0"));
        }
        if self.shards.iter().all(|s| s.read().unwrap().is_empty()) {
            return Err(Status::failed_precondition("store not initialized"));
        }
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
        Ok(Response::new(SearchResponse { results: top }))
    }
}

pub async fn serve(addr: SocketAddr) -> Result<(), Box<dyn std::error::Error>> {
    Server::builder()
        .add_service(VectorServiceServer::new(VectorServer::default()))
        .serve(addr)
        .await?;
    Ok(())
}
