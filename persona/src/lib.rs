use pyo3::prelude::*;
use tracing::instrument;

const PERSONALITIES: &[&str] = &["albedo", "citrinitas", "nigredo", "rubedo"];

#[pyfunction]
#[instrument]
fn list_personalities() -> Vec<&'static str> {
    let mut v = PERSONALITIES.to_vec();
    v.sort();
    v
}

#[pyfunction]
#[instrument]
fn generate_response(layer: &str, text: &str) -> PyResult<String> {
    if PERSONALITIES.contains(&layer) {
        Ok(format!("[{layer}] {text}"))
    } else {
        Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "unknown layer",
        ))
    }
}

#[pymodule]
fn neoabzu_persona_layers(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    let _ = neoabzu_instrumentation::init_tracing("persona");
    m.add_function(wrap_pyfunction!(list_personalities, m)?)?;
    m.add_function(wrap_pyfunction!(generate_response, m)?)?;
    Ok(())
}
