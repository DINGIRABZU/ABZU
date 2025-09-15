use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

/// Wraps a Python callable as a connector plugin.
///
/// The callable must accept a question string and return a list of
/// dictionaries containing at least a `text` field.
#[pyclass]
pub struct FuncConnector {
    callable: Py<PyAny>,
}

#[pymethods]
impl FuncConnector {
    #[new]
    pub fn new(callable: Py<PyAny>) -> Self {
        Self { callable }
    }

    /// Execute the wrapped callable and return document dictionaries.
    pub fn retrieve(&self, py: Python<'_>, question: &str) -> PyResult<Vec<Py<PyDict>>> {
        let result = self.callable.call1(py, (question,))?;
        let list: &PyList = result.downcast(py)?;
        Ok(list
            .iter()
            .filter_map(|d| d.downcast::<PyDict>().ok().map(|p| p.into()))
            .collect())
    }
}
