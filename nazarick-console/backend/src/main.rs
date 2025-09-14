use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Path, Query,
    },
    http::StatusCode,
    response::IntoResponse,
    routing::get,
    Router,
};
use futures::{SinkExt, StreamExt};
use neoabzu_chakrapulse::{emit_pulse, subscribe_chakra};
use std::{collections::HashMap, net::SocketAddr, time::Duration};
use tokio::sync::broadcast;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let (tx, _) = broadcast::channel::<String>(100);

    {
        let tx = tx.clone();
        std::thread::spawn(move || {
            let rx = subscribe_chakra();
            for pulse in rx.iter() {
                let msg = format!("chakra:{}:{}", pulse.source, pulse.ok);
                let _ = tx.send(msg);
            }
        });
    }

    tokio::spawn(async move {
        loop {
            emit_pulse("backend", true);
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    });

    // synthetic log stream
    tokio::spawn({
        let tx = tx.clone();
        async move {
            let mut n = 0u64;
            loop {
                let _ = tx.send(format!("log:agent{0}:entry {0}", n % 3));
                n += 1;
                tokio::time::sleep(Duration::from_secs(2)).await;
            }
        }
    });

    let app = Router::new().route(
        "/ws/:agent",
        get({
            let tx = tx.clone();
            move |ws: WebSocketUpgrade,
                  Path(agent): Path<String>,
                  Query(params): Query<HashMap<String, String>>| {
                ws_handler(ws, agent, params.get("token").cloned(), tx.clone())
            }
        }),
    );

    let addr = SocketAddr::from(([0, 0, 0, 0], 3001));
    println!("listening on {addr}");
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn ws_handler(
    ws: WebSocketUpgrade,
    agent: String,
    token: Option<String>,
    tx: broadcast::Sender<String>,
) -> Result<impl IntoResponse, StatusCode> {
    if token.as_deref() != Some("demo") {
        return Err(StatusCode::UNAUTHORIZED);
    }
    Ok(ws.on_upgrade(move |socket| websocket(socket, agent, tx)))
}

async fn websocket(stream: WebSocket, agent: String, tx: broadcast::Sender<String>) {
    let (mut sender, mut receiver) = stream.split();
    let mut rx = tx.subscribe();

    let send_task = tokio::spawn(async move {
        while let Ok(msg) = rx.recv().await {
            if sender.send(Message::Text(msg)).await.is_err() {
                break;
            }
        }
    });

    while let Some(Ok(Message::Text(text))) = receiver.next().await {
        let _ = tx.send(format!("log:{agent}:{text}"));
    }

    send_task.abort();
}
