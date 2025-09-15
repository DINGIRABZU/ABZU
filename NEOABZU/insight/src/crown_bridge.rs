use crate::semantics;
use pyo3::prelude::*;
#[cfg(feature = "tracing")]
use tracing::instrument;

/// Call the Crown Router's semantic bridge via Python bindings.
#[cfg_attr(feature = "tracing", instrument(skip(py)))]
pub fn call_crown_semantic(py: Python<'_>, text: &str) -> PyResult<Vec<(String, f32)>> {
    match py.import_bound("neoabzu_crown") {
        Ok(module) => {
            let response = module.call_method1("insight_semantic", (text,))?;
            response.extract()
        }
        Err(_) => Ok(semantics(text)),
    }
}

/// Return semantic scores computed by the Crown Router.
#[cfg_attr(feature = "tracing", instrument(skip(py)))]
#[pyfunction]
pub fn crown_semantic(py: Python<'_>, text: &str) -> PyResult<Vec<(String, f32)>> {
    call_crown_semantic(py, text)
}
