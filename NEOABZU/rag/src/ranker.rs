use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::{cosine, embed};

/// Cosine-similarity ranking strategy mirroring the default behaviour.
#[pyclass]
pub struct CosineRanker;

#[pymethods]
impl CosineRanker {
    #[new]
    pub fn new() -> Self {
        Self
    }

    /// Rank documents by cosine similarity to the question.
    pub fn rank(&self, py: Python<'_>, question: &str, docs: &PyList) -> PyResult<Vec<Py<PyDict>>> {
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
            let dict: Py<PyDict> = obj.extract(py)?;
            scored.push((score, dict));
        }
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
        Ok(scored.into_iter().map(|(_, d)| d).collect())
    }
}
