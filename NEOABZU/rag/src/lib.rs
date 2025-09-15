//! Retrieval-augmented generation utilities.
//!
//! Enable telemetry with:
//! `cargo test -p neoabzu-rag --features opentelemetry`
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

mod connector;
mod ranker;
mod orchestrator;

pub use connector::FuncConnector;
pub use ranker::CosineRanker;
pub use orchestrator::Orchestrator;

pub(crate) const EMBED_DIM: usize = 16;

pub(crate) fn embed(text: &str) -> [f32; EMBED_DIM] {
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

pub(crate) fn cosine(a: &[f32; EMBED_DIM], b: &[f32; EMBED_DIM]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    dot
}

#[cfg_attr(
    feature = "tracing",
    tracing::instrument(skip(py, memory, connectors, ranker))
)]
#[pyfunction]
#[pyo3(signature = (question, memory, connectors=None, top_n=5, ranker=None))]
pub fn merge_documents(
    py: Python<'_>,
    question: &str,
    memory: &PyList,
    connectors: Option<&PyList>,
    top_n: usize,
    ranker: Option<&PyAny>,
) -> PyResult<Vec<Py<PyDict>>> {
    let mut collected: Vec<Py<PyDict>> = Vec::new();
    let sources = [("memory", Some(memory)), ("connector", connectors)];
    for (source, list_opt) in sources.iter() {
        if let Some(list) = list_opt {
            for item in list.iter() {
                if let Ok(meta) = item.downcast::<PyDict>() {
                    let out = PyDict::new(py);
                    for (k, v) in meta {
                        out.set_item(k, v)?;
                    }
                    out.set_item("source", source)?;
                    collected.push(out.into());
                }
            }
        }
    }

    let docs = PyList::new(py, collected);
    if let Some(r) = ranker {
        let callable: &PyAny = if r.hasattr("rank")? {
            r.getattr("rank")?
        } else {
            r
        };
        let ranked = callable.call1((question, docs))?;
        let ranked_list: &PyList = ranked.downcast()?;
        return Ok(ranked_list
            .iter()
            .take(top_n)
            .filter_map(|d| d.downcast::<PyDict>().ok().map(|p| p.into()))
            .collect());
    }

    let q_emb = embed(question);
    let mut scored: Vec<(f32, Py<PyDict>)> = Vec::new();
    for doc in docs.iter() {
        let meta: &PyDict = doc.downcast()?;
        let text: String = meta
            .get_item("text")?
            .and_then(|o| o.extract().ok())
            .unwrap_or_default();
        let emb = embed(&text);
        let score = cosine(&q_emb, &emb);
        meta.set_item("score", score)?;
        let obj = meta.to_object(py);
        let dict: Py<PyDict> = obj.extract::<Py<PyDict>>(py)?;
        scored.push((score, dict));
    }
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    Ok(scored.into_iter().take(top_n).map(|(_, d)| d).collect())
}

#[cfg_attr(feature = "tracing", tracing::instrument(skip(py, connectors, ranker)))]
#[pyfunction]
#[pyo3(signature = (question, top_n=5, connectors=None, ranker=None))]
pub fn retrieve_top(
    py: Python<'_>,
    question: &str,
    top_n: usize,
    connectors: Option<&PyList>,
    ranker: Option<&PyAny>,
) -> PyResult<Vec<Py<PyDict>>> {
    Orchestrator::retrieve(py, question, connectors, ranker, top_n)
}

/// Minimal orchestrator that gathers documents from memory and optional connectors.
///
/// The orchestrator mirrors the behaviour of the legacy Python implementation by
/// collecting documents via [`retrieve_top`] and returning a dictionary containing
/// the selected model and aggregated documents.
#[pyclass]
pub struct MoGEOrchestrator;

#[pymethods]
impl MoGEOrchestrator {
    #[new]
    pub fn new() -> Self {
        Self
    }

    #[pyo3(signature = (text, emotion_data, *, qnl_data=None, text_modality=true, voice_modality=false, music_modality=false, documents=None, **kwargs))]
    pub fn route(
        &self,
        py: Python<'_>,
        text: &str,
        emotion_data: &PyDict,
        qnl_data: Option<&PyDict>,
        text_modality: bool,
        voice_modality: bool,
        music_modality: bool,
        documents: Option<&PyAny>,
        kwargs: Option<&PyDict>,
    ) -> PyResult<Py<PyDict>> {
        let _ = (
            emotion_data,
            qnl_data,
            text_modality,
            voice_modality,
            music_modality,
        );

        let top_n = kwargs
            .and_then(|k| k.get_item("top_n").ok().flatten())
            .and_then(|o| o.extract().ok())
            .unwrap_or(5usize);

        let connectors = kwargs
            .and_then(|k| k.get_item("connectors").ok().flatten())
            .and_then(|v| v.downcast::<PyList>().ok());

        let ranker = kwargs.and_then(|k| k.get_item("ranker").ok().flatten());

        let documents = if let Some(doc_any) = documents {
            doc_any
                .downcast::<PyList>()
                .map(|l| l.to_object(py))
                .unwrap_or_else(|_| PyList::empty(py).to_object(py))
        } else {
            let docs = retrieve_top(py, text, top_n, connectors, ranker)?;
            PyList::new(py, docs).to_object(py)
        };

        let result = PyDict::new(py);
        result.set_item("model", "basic-rag")?;
        result.set_item("documents", documents)?;
        Ok(result.into())
    }
}

#[pymodule]
fn neoabzu_rag(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(merge_documents, m)?)?;
    m.add_function(wrap_pyfunction!(retrieve_top, m)?)?;
    m.add_class::<MoGEOrchestrator>()?;
    m.add_class::<FuncConnector>()?;
    m.add_class::<CosineRanker>()?;
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
            let res = retrieve_top(py, "abc", 1, None, None).unwrap();
            let first: &PyDict = res[0].as_ref(py);
            let text: String = first.get_item("text").unwrap().unwrap().extract().unwrap();
            assert_eq!(text, "abc");
        });
    }
}
