use std::net::SocketAddr;

use crate::proto::vector_service_server::{VectorService, VectorServiceServer};
use crate::proto::{InitRequest, InitResponse, SearchRequest, SearchResponse, SearchResult};
use tonic::{transport::Server, Request, Response, Status};

#[derive(Default)]
pub struct VectorServer;

#[tonic::async_trait]
impl VectorService for VectorServer {
    async fn init(&self, _request: Request<InitRequest>) -> Result<Response<InitResponse>, Status> {
        Ok(Response::new(InitResponse {
            message: "ok".to_string(),
        }))
    }

    async fn search(&self, request: Request<SearchRequest>) -> Result<Response<SearchResponse>, Status> {
        let req = request.into_inner();
        let results = (0..req.top_n)
            .map(|i| SearchResult {
                text: format!("{}{}", req.text, i),
                score: 1.0,
                embedding: vec![0.0, 0.0],
            })
            .collect();
        Ok(Response::new(SearchResponse { results }))
    }
}

pub async fn serve(addr: SocketAddr) -> Result<(), Box<dyn std::error::Error>> {
    Server::builder()
        .add_service(VectorServiceServer::new(VectorServer::default()))
        .serve(addr)
        .await?;
    Ok(())
}
