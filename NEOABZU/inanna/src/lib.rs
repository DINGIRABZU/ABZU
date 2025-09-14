use pyo3::prelude::*;
use neoabzu_chakrapulse::emit_pulse;

#[pyfunction]
pub fn invoke_spell(name: &str) -> PyResult<String> {
    emit_pulse("inanna", true);
    Ok(format!("spell:{name}"))
}

#[pymodule]
fn neoabzu_inanna(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(invoke_spell, m)?)?;
    Ok(())
}
