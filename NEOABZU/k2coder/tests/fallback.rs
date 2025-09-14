use std::io::{Read, Write};
use std::net::TcpListener;
use std::thread;

use neoabzu_kimicho::{fallback_k2, init_kimicho};

#[test]
fn crown_failure_switches_to_k2_coder() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let addr = listener.local_addr().unwrap();
    thread::spawn(move || {
        if let Ok((mut stream, _)) = listener.accept() {
            let mut buf = [0u8; 1024];
            let _ = stream.read(&mut buf);
            let body = r#"{\"text\":\"k2 diff\"}"#;
            let response = format!(
                "HTTP/1.1 200 OK\r\ncontent-type: application/json\r\ncontent-length: {}\r\n\r\n{}",
                body.len(), body
            );
            let _ = stream.write_all(response.as_bytes());
        }
    });

    init_kimicho(Some(format!("http://{}", addr)));
    let out = fallback_k2("fn main() {}").expect("fallback succeeded");
    assert_eq!(out, "k2 diff");
}

#[test]
fn crown_failure_reports_error_when_k2_unreachable() {
    init_kimicho(Some("http://127.0.0.1:1".to_string()));
    let err = fallback_k2("fn main() {}").expect_err("request should fail");
    assert!(err.to_string().contains("K2 request failed"));
}
