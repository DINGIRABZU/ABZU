use pyo3::prelude::*;
use pyo3::types::PyDict;
use neoabzu_chakrapulse::emit_pulse;

fn kimicho_fallback(py: Python<'_>, text: &str) -> PyResult<Py<PyDict>> {
    let kimi = PyModule::import(py, "neoabzu_kimicho")?;
    let txt: String = kimi.call_method1("fallback_k2", (text,))?.extract()?;
    let out = PyDict::new(py);
    out.set_item("text", txt)?;
    Ok(out.into())
}

#[pyfunction]
pub fn route(py: Python<'_>, text: &str, emotion: &str) -> PyResult<Py<PyDict>> {
    let crown = match PyModule::import(py, "neoabzu_crown") {
        Ok(m) => m,
        Err(_) => return kimicho_fallback(py, text),
    };
    let emo = PyDict::new(py);
    emo.set_item("emotion", emotion)?;
    match crown.call_method("route_decision", (text, emo), None) {
        Ok(obj) => obj.extract(),
        Err(_) => kimicho_fallback(py, text),
    }
}

#[pyfunction]
fn health_pulse() {
    emit_pulse("razar", true);
}

#[pymodule]
fn neoabzu_razar(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(route, m)?)?;
    m.add_function(wrap_pyfunction!(health_pulse, m)?)?;
    // ensure dependent modules load if available
    PyModule::import(py, "neoabzu_crown").ok();
    PyModule::import(py, "neoabzu_kimicho").ok();
    Ok(())
}
