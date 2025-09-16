use neoabzu_vector::proto::vector_service_client::VectorServiceClient;
use neoabzu_vector::proto::{InitRequest, SearchRequest};
use neoabzu_vector::serve;
use once_cell::sync::Lazy;
use std::fs::{self, File};
use std::io::Write;
use std::net::TcpListener;
use tokio::{
    sync::Mutex,
    time::{sleep, Duration},
};

fn available_addr() -> std::net::SocketAddr {
    TcpListener::bind("127.0.0.1:0")
        .unwrap()
        .local_addr()
        .unwrap()
}

static TEST_MUTEX: Lazy<Mutex<()>> = Lazy::new(|| Mutex::new(()));

#[tokio::test]
async fn init_and_search() {
    let _guard = TEST_MUTEX.lock().await;
    let dir = tempfile::tempdir().unwrap();
    let store_path = dir.path().join("store.json");
    let mut f = File::create(&store_path).unwrap();
    f.write_all(b"[\"alpha\", \"beta\"]").unwrap();
    std::env::set_var("NEOABZU_VECTOR_STORE", &store_path);
    let db_path = dir.path().join("db");
    std::env::set_var("NEOABZU_VECTOR_DB", &db_path);

    let addr = available_addr();
    let server = tokio::spawn(async move {
        serve(addr).await.unwrap();
    });
    sleep(Duration::from_millis(100)).await;

    let endpoint = format!("http://{}", addr);
    let mut client = VectorServiceClient::connect(endpoint).await.unwrap();

    assert!(client
        .search(SearchRequest {
            text: "alpha".into(),
            top_n: 1,
        })
        .await
        .is_err());

    let init = client.init(InitRequest {}).await.unwrap().into_inner();
    assert!(init.message.contains("loaded"));

    let resp = client
        .search(SearchRequest {
            text: "alpha".into(),
            top_n: 1,
        })
        .await
        .unwrap()
        .into_inner();
    assert_eq!(resp.results[0].text, "alpha");

    drop(client);
    server.abort();
    let _ = server.await;
    std::env::remove_var("NEOABZU_VECTOR_DB");
    std::env::remove_var("NEOABZU_VECTOR_STORE");
}

#[tokio::test]
async fn init_falls_back_to_persistent_store() {
    let _guard = TEST_MUTEX.lock().await;
    let dir = tempfile::tempdir().unwrap();
    let store_path = dir.path().join("store.json");
    let mut f = File::create(&store_path).unwrap();
    f.write_all(b"[\"alpha\", \"beta\"]").unwrap();
    let db_path = dir.path().join("db");
    std::env::set_var("NEOABZU_VECTOR_STORE", &store_path);
    std::env::set_var("NEOABZU_VECTOR_DB", &db_path);

    let addr = available_addr();
    let server = tokio::spawn(async move {
        serve(addr).await.unwrap();
    });
    sleep(Duration::from_millis(100)).await;

    let endpoint = format!("http://{}", addr);
    let mut client = VectorServiceClient::connect(endpoint.clone())
        .await
        .unwrap();
    client.init(InitRequest {}).await.unwrap();
    drop(client);
    server.abort();
    let _ = server.await;
    sleep(Duration::from_millis(100)).await;

    // Remove the dataset and ensure init still succeeds by loading persisted entries.
    fs::remove_file(&store_path).unwrap();

    let addr2 = available_addr();
    let server2 = tokio::spawn(async move {
        serve(addr2).await.unwrap();
    });
    sleep(Duration::from_millis(100)).await;

    let mut client = VectorServiceClient::connect(format!("http://{}", addr2))
        .await
        .unwrap();

    let init = client.init(InitRequest {}).await.unwrap().into_inner();
    assert!(init.message.contains("loaded 2"));

    let resp = client
        .search(SearchRequest {
            text: "beta".into(),
            top_n: 1,
        })
        .await
        .unwrap()
        .into_inner();
    assert_eq!(resp.results[0].text, "beta");

    drop(client);
    server2.abort();
    let _ = server2.await;
    std::env::remove_var("NEOABZU_VECTOR_DB");
    std::env::remove_var("NEOABZU_VECTOR_STORE");
}
