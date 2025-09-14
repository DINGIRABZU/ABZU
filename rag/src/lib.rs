use metrics::{counter, histogram};
use neoabzu_memory::MemoryBundle;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::time::Instant;
use tracing::instrument;

const EMBED_DIM: usize = 16;

fn embed(text: &str) -> [f32; EMBED_DIM] {
    let mut v = [0f32; EMBED_DIM];
    for (i, b) in text.bytes().enumerate() {
        v[i % EMBED_DIM] += b as f32 / 255.0;
    }
    let norm: f32 = v.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for x in &mut v {
            *x /= norm;
        }
    }
    v
}

fn cosine(a: &[f32; EMBED_DIM], b: &[f32; EMBED_DIM]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

#[pyfunction]
#[pyo3(signature = (question, top_n=5))]
#[instrument(skip(py))]
pub fn retrieve_top(py: Python<'_>, question: &str, top_n: usize) -> PyResult<Vec<Py<PyDict>>> {
    let start = Instant::now();
    let mut bundle = MemoryBundle::new();
    bundle.initialize(py)?;
    let q_dict = bundle.query(py, question)?;
    let data = q_dict.as_ref(py);
    let vector_any = data
        .get_item("vector")?
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("vector"))?;
    let vector_list: &PyList = vector_any.downcast()?;
    let q_emb = embed(question);
    let mut scored: Vec<(f32, Py<PyDict>)> = Vec::new();
    for item in vector_list.iter() {
        if let Ok(meta) = item.downcast::<PyDict>() {
            let text: String = meta
                .get_item("text")?
                .and_then(|o| o.extract().ok())
                .unwrap_or_default();
            let emb = embed(&text);
            let score = cosine(&q_emb, &emb);
            let out = PyDict::new(py);
            for (k, v) in meta {
                out.set_item(k, v)?;
            }
            out.set_item("score", score)?;
            scored.push((score, out.into()));
        }
    }
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    counter!("neoabzu_rag_retrieve_top_total", 1);
    histogram!(
        "neoabzu_rag_retrieve_top_latency_seconds",
        start.elapsed().as_secs_f64()
    );
    Ok(scored.into_iter().take(top_n).map(|(_, d)| d).collect())
}

#[pymodule]
fn neoabzu_rag(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    let _ = neoabzu_instrumentation::init_tracing("rag");
    m.add_function(wrap_pyfunction!(retrieve_top, m)?)?;
    Ok(())
}
