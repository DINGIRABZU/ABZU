use neoabzu_vector::proto::vector_service_client::VectorServiceClient;
use neoabzu_vector::proto::{InitRequest, SearchRequest};
use neoabzu_vector::serve;
use tokio::time::{sleep, Duration};

#[tokio::test]
async fn init_and_search() {
    let addr: std::net::SocketAddr = "127.0.0.1:50051".parse().unwrap();
    let server = tokio::spawn(async move {
        serve(addr).await.unwrap();
    });
    sleep(Duration::from_millis(100)).await;

    let endpoint = format!("http://{}", addr);
    let mut client = VectorServiceClient::connect(endpoint).await.unwrap();

    let init = client.init(InitRequest {}).await.unwrap().into_inner();
    assert_eq!(init.message, "ok");

    let resp = client
        .search(SearchRequest {
            text: "a".into(),
            top_n: 2,
        })
        .await
        .unwrap()
        .into_inner();
    assert_eq!(resp.results.len(), 2);
    assert_eq!(resp.results[0].text, "a0");

    server.abort();
}
