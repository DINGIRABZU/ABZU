// Patent pending – see PATENTS.md
//! Kimicho fallback client delegating code generation to K2 Coder.

use metrics::{counter, histogram};
use once_cell::sync::Lazy;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::sync::Mutex;
use std::time::{Duration, Instant};
#[cfg(feature = "tracing")]
use tracing::instrument;

static ENDPOINT: Lazy<Mutex<String>> = Lazy::new(|| {
    Mutex::new(std::env::var("KIMI_K2_URL").unwrap_or_else(|_| "http://localhost:8004".to_string()))
});

/// Initialize Kimicho with an optional endpoint override.
#[pyfunction]
#[cfg_attr(feature = "tracing", instrument(skip(endpoint)))]
pub fn init_kimicho(endpoint: Option<String>) {
    if let Some(ep) = endpoint {
        *ENDPOINT.lock().expect("lock poisoned") = ep;
    }
    counter!("neoabzu_kimicho_init_total", 1);
}

/// Call the K2 Coder service and return its response text.
#[pyfunction]
#[cfg_attr(feature = "tracing", instrument)]
pub fn fallback_k2(prompt: &str) -> PyResult<String> {
    let start = Instant::now();
    let endpoint = ENDPOINT.lock().expect("lock poisoned").clone();
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(10))
        .build()
        .map_err(|e| PyRuntimeError::new_err(format!("K2 client init failed: {e}")))?;
    let resp = client
        .post(&endpoint)
        .json(&serde_json::json!({ "prompt": prompt }))
        .send()
        .and_then(|r| r.error_for_status())
        .map_err(|e| PyRuntimeError::new_err(format!("K2 request failed: {e}")))?;
    let text = resp
        .text()
        .map_err(|e| PyRuntimeError::new_err(format!("K2 request failed: {e}")))?;
    let value = serde_json::from_str::<serde_json::Value>(&text)
        .ok()
        .and_then(|v| {
            v.get("text")
                .and_then(|s| s.as_str().map(|s| s.to_string()))
        })
        .unwrap_or(text);
    counter!("neoabzu_kimicho_fallback_k2_total", 1);
    histogram!(
        "neoabzu_kimicho_fallback_k2_latency_seconds",
        start.elapsed().as_secs_f64()
    );
    Ok(value)
}

#[pymodule]
fn neoabzu_kimicho(_py: Python<'_>, m: &Bound<PyModule>) -> PyResult<()> {
    #[cfg(feature = "tracing")]
    let _ = neoabzu_instrumentation::init_tracing("kimicho");
    m.add_function(wrap_pyfunction!(init_kimicho, m)?)?;
    m.add_function(wrap_pyfunction!(fallback_k2, m)?)?;
    Ok(())
}
