//! Retrieval-augmented generation utilities.
//!
//! Enable telemetry with:
//! `cargo test -p neoabzu-rag --features opentelemetry`
use neoabzu_memory::MemoryBundle;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

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
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    dot
}

#[cfg_attr(feature = "tracing", tracing::instrument(skip(py)))]
#[pyfunction]
#[pyo3(signature = (question, top_n=5, connectors=None))]
pub fn retrieve_top(
    py: Python<'_>,
    question: &str,
    top_n: usize,
    connectors: Option<&PyList>,
) -> PyResult<Vec<Py<PyDict>>> {
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
            out.set_item("source", "memory")?;
            scored.push((score, out.into()));
        }
    }

    if let Some(conn_list) = connectors {
        for conn in conn_list.iter() {
            let callable: &PyAny = if conn.hasattr("retrieve")? {
                conn.getattr("retrieve")?
            } else {
                conn
            };
            if !callable.is_callable() {
                continue;
            }
            let fetched = callable.call1((question,))?;
            let items: &PyList = fetched.downcast()?;
            for item in items.iter() {
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
                    out.set_item("source", "connector")?;
                    scored.push((score, out.into()));
                }
            }
        }
    }

    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    Ok(scored.into_iter().take(top_n).map(|(_, d)| d).collect())
}

#[pymodule]
fn neoabzu_rag(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(retrieve_top, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{cosine, embed, retrieve_top};
    use pyo3::prelude::*;
    use pyo3::types::{PyDict, PyModule};

    #[test]
    fn cosine_self_is_one() {
        let v = embed("abc");
        assert!((cosine(&v, &v) - 1.0).abs() < 1e-6);
    }

    fn setup(py: Python<'_>) {
        let sys = py.import("sys").unwrap();
        let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();
        let agents = PyModule::new(py, "agents").unwrap();
        modules.set_item("agents", agents).unwrap();
        let event_code = r#"
events = []
def emit_event(actor, action, metadata):
    events.append((actor, action, metadata))
"#;
        let event_bus = PyModule::from_code(py, event_code, "", "event_bus").unwrap();
        modules.set_item("agents.event_bus", event_bus).unwrap();
        let vector_code = r#"
def query_vectors(*a, **k):
    return [{'text':'abc'}]
"#;
        let vector_mod = PyModule::from_code(py, vector_code, "", "vector_memory").unwrap();
        modules.set_item("vector_memory", vector_mod).unwrap();
    }

    #[test]
    fn retrieve_top_returns_expected() {
        Python::with_gil(|py| {
            setup(py);
            let res = retrieve_top(py, "abc", 1, None).unwrap();
            let first: &PyDict = res[0].as_ref(py);
            let text: String = first.get_item("text").unwrap().unwrap().extract().unwrap();
            assert_eq!(text, "abc");
        });
    }
}
