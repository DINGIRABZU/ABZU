use neoabzu_memory::MemoryBundle;
use pyo3::prelude::*;
use pyo3::types::PyDict;
#[cfg(feature = "tracing")]
use tracing::instrument;

#[pyfunction]
#[cfg_attr(feature = "tracing", instrument(skip(py)))]
fn route_query(py: Python<'_>, question: &str) -> PyResult<Py<PyDict>> {
    let mut bundle = MemoryBundle::new();
    bundle.initialize(py)?;
    bundle.query(py, question)
}

#[pyfunction]
#[pyo3(signature = (text, emotion_data, documents=None))]
#[cfg_attr(feature = "tracing", instrument(skip(py, emotion_data, documents)))]
fn route_decision(
    py: Python<'_>,
    text: &str,
    emotion_data: &PyDict,
    documents: Option<Py<PyDict>>,
) -> PyResult<Py<PyDict>> {
    let memory = route_query(py, text)?;
    let emotion = emotion_data
        .get_item("emotion")?
        .and_then(|v| v.extract::<String>().ok())
        .unwrap_or_else(|| "neutral".to_string());
    let decision = PyDict::new_bound(py);
    decision.set_item("model", "default")?;
    decision.set_item("tts_backend", "voice_v1")?;
    decision.set_item("avatar_style", "standard")?;
    decision.set_item("aura", emotion)?;
    decision.set_item("memory", memory)?;
    if let Some(d) = documents {
        decision.set_item("documents", d)?;
    }
    Ok(decision.into())
}

#[pymodule]
fn neoabzu_crown(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    #[cfg(feature = "tracing")]
    let _ = neoabzu_instrumentation::init_tracing("crown");
    m.add_function(wrap_pyfunction!(route_query, m)?)?;
    m.add_function(wrap_pyfunction!(route_decision, m)?)?;
    PyModule::import(py, "neoabzu_memory")?;
    Ok(())
}
