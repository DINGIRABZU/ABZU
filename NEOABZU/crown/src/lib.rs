use std::time::Instant;

use neoabzu_core::{evaluate, reduce_inevitable_with_journey};
use neoabzu_insight::{analyze as insight_analyze, embedding as insight_embed};
use neoabzu_memory::MemoryBundle;
use neoabzu_rag::{retrieve_top, MoGEOrchestrator};
use pyo3::{prelude::*, wrap_pyfunction};
use pyo3::types::{PyDict, PyList};

fn select_store(archetype: &str) -> &str {
    match archetype.to_lowercase().as_str() {
        "sage" | "hero" => "tech",
        "warrior" | "orphan" | "caregiver" | "citrinitas" => "ritual",
        "jester" | "everyman" => "music",
        _ => "tech",
    }
}

#[pyfunction]
fn route_query(py: Python<'_>, question: &str, archetype: &str) -> PyResult<PyObject> {
    let _ = select_store(archetype);
    let res = retrieve_top(py, question, 5, None)?;
    Ok(PyList::new(py, res).into_py(py))
}

#[derive(Debug)]
struct ExpressionOptions {
    tts_backend: String,
    avatar_style: String,
    aura: String,
}

fn decide_expression_options(emotion: &str) -> ExpressionOptions {
    let emotion = emotion.to_lowercase();
    let tts_backend = if matches!(emotion.as_str(), "anger" | "fear") {
        "bark"
    } else {
        "gtts"
    }
    .to_string();
    let avatar_style = match emotion.as_str() {
        "joy" => "Soprano",
        "sadness" => "Baritone",
        _ => "Androgynous",
    }
    .to_string();
    ExpressionOptions {
        tts_backend,
        avatar_style,
        aura: emotion,
    }
}

#[pyfunction]
#[pyo3(signature = (text, emotion_data, orchestrator=None, validator=None, documents=None))]
pub fn route_decision(
    py: Python<'_>,
    text: &str,
    emotion_data: &PyDict,
    orchestrator: Option<&PyAny>,
    validator: Option<&PyAny>,
    documents: Option<&PyAny>,
) -> PyResult<Py<PyDict>> {
    let _ = (orchestrator, validator); // legacy params for compatibility
    let start = Instant::now();

    let docs_obj = if let Some(d) = documents {
        d.to_object(py)
    } else {
        let orch = MoGEOrchestrator::new();
        let routed = orch.route(py, text, emotion_data, None, false, false, false, None, None)?;
        routed
            .as_ref(py)
            .get_item("documents")?
            .map(|o| o.to_object(py))
            .unwrap_or_else(|| py.None())
    };

    let mut bundle = MemoryBundle::new();
    bundle.initialize(py)?;
    let mem = bundle.query(py, text)?;

    let core_output = evaluate(py, text);
    let report = insight_analyze(text);
    let words: Vec<String> = report
        .get("words")
        .map(|v| v.iter().map(|(w, _)| w.clone()).collect())
        .unwrap_or_default();
    let bigrams: Vec<String> = report
        .get("bigrams")
        .map(|v| v.iter().map(|(b, _)| b.clone()).collect())
        .unwrap_or_default();
    let embedding = insight_embed(text);

    let emotion: String = emotion_data
        .get_item("emotion")?
        .and_then(|o| o.extract().ok())
        .unwrap_or_else(|| "neutral".to_string());
    let opts = decide_expression_options(&emotion);

    let result = PyDict::new(py);
    result.set_item("model", "basic-rag")?;
    result.set_item("tts_backend", opts.tts_backend)?;
    result.set_item("avatar_style", opts.avatar_style)?;
    result.set_item("aura", opts.aura)?;
    result.set_item("documents", docs_obj)?;
    result.set_item("memory", mem)?;
    result.set_item("core", core_output)?;
    result.set_item("insight_words", words)?;
    result.set_item("insight_bigrams", bigrams)?;
    result.set_item("insight_embedding", embedding)?;
    result.set_item("latency_seconds", start.elapsed().as_secs_f64())?;
    Ok(result.into())
}

#[pyfunction]
pub fn route_inevitability(py: Python<'_>, expr: &str) -> PyResult<Py<PyDict>> {
    let (inevitability, journey) = reduce_inevitable_with_journey(expr);
    let result = PyDict::new(py);
    result.set_item("inevitability", inevitability)?;
    let journey_py: Vec<String> = journey.iter().map(|s| format!("{:?}", s)).collect();
    result.set_item("journey", journey_py)?;
    Ok(result.into())
}

#[pyfunction]
pub fn query_memory(py: Python<'_>, text: &str) -> PyResult<Py<PyDict>> {
    let mut bundle = MemoryBundle::new();
    bundle.initialize(py)?;
    bundle.query(py, text)
}

#[pyfunction]
pub fn insight_embedding(text: &str) -> PyResult<Vec<f32>> {
    Ok(insight_embed(text))
}

#[pymodule]
fn neoabzu_crown(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(route_query, m)?)?;
    m.add_function(wrap_pyfunction!(route_decision, m)?)?;
    m.add_function(wrap_pyfunction!(route_inevitability, m)?)?;
    m.add_function(wrap_pyfunction!(query_memory, m)?)?;
    m.add_function(wrap_pyfunction!(insight_embedding, m)?)?;
    let _ = py; // reserve for future use
    Ok(())
}
