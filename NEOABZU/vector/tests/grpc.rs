use neoabzu_vector::proto::vector_service_client::VectorServiceClient;
use neoabzu_vector::proto::{InitRequest, SearchRequest};
use neoabzu_vector::serve;
use std::fs::File;
use std::io::Write;
use tokio::time::{sleep, Duration};

#[tokio::test]
async fn init_and_search() {
    let dir = tempfile::tempdir().unwrap();
    let store_path = dir.path().join("store.json");
    let mut f = File::create(&store_path).unwrap();
    f.write_all(b"[\"alpha\", \"beta\"]").unwrap();
    std::env::set_var("NEOABZU_VECTOR_STORE", &store_path);

    let addr: std::net::SocketAddr = "127.0.0.1:50051".parse().unwrap();
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

    server.abort();
}
