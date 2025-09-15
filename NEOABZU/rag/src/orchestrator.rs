use neoabzu_memory::MemoryBundle;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};

/// Core retrieval orchestrator.
///
/// Gathers documents from the [`MemoryBundle`] and optional connector plugins,
/// tagging each item with its source and applying an optional ranking
/// strategy. Mirrors the behaviour of the Python ``rag.orchestrator`` module.
pub struct Orchestrator;

impl Orchestrator {
    pub fn retrieve(
        py: Python<'_>,
        question: &str,
        connectors: Option<&PyList>,
        ranker: Option<&PyAny>,
        top_n: usize,
    ) -> PyResult<Vec<Py<PyDict>>> {
        let mut bundle = MemoryBundle::new();
        bundle.initialize(py)?;
        let q_dict = bundle.query(py, question)?;
        let data = q_dict.as_ref(py);
        let vector_any = data
            .get_item("vector")?
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("vector"))?;
        let memory_list: &PyList = vector_any.downcast()?;

        let mut connector_accum: Vec<Py<PyDict>> = Vec::new();
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
                        connector_accum.push(meta.into());
                    }
                }
            }
        }

        let connector_list = PyList::new(py, connector_accum);
        crate::merge_documents(
            py,
            question,
            memory_list,
            Some(connector_list),
            top_n,
            ranker,
        )
    }
}
