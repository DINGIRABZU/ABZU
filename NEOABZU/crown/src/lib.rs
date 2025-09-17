use std::time::Instant;

use neoabzu_chakrapulse::emit_pulse;
use neoabzu_core::{evaluate, reduce_inevitable_with_journey};
use neoabzu_insight::{
    analyze as insight_analyze, embedding as insight_embed, semantics as insight_semantics,
};
use neoabzu_memory::MemoryBundle;
use neoabzu_rag::{retrieve_top, MoGEOrchestrator};
use pyo3::exceptions::PyValueError;
use pyo3::types::{PyDict, PyList};
use pyo3::{prelude::*, wrap_pyfunction};
use std::fs;
use std::path::PathBuf;

fn select_store(archetype: &str) -> &str {
    match archetype.to_lowercase().as_str() {
        "sage" | "hero" => "tech",
        "warrior" | "orphan" | "caregiver" | "citrinitas" => "ritual",
        "jester" | "everyman" => "music",
        _ => "tech",
    }
}

const IDENTITY_FILE: &str = "data/identity.json";
const MISSION_DOC: &str = "docs/project_mission_vision.md";
const PERSONA_DOC: &str = "docs/persona_api_guide.md";
const DOCTRINE_DOCS: [&str; 3] = [
    "docs/The_Absolute_Protocol.md",
    "docs/system_blueprint.md",
    "docs/awakening_overview.md",
];

#[pyfunction]
fn route_query(py: Python<'_>, question: &str, archetype: &str) -> PyResult<PyObject> {
    if question.trim().is_empty() {
        return Err(PyValueError::new_err("question cannot be empty"));
    }
    let _ = select_store(archetype);
    let res = retrieve_top(py, question, 5, None, None)?;
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
    let start = Instant::now();

    if text.trim().is_empty() {
        return Err(PyValueError::new_err("text cannot be empty"));
    }

    // determine model and documents via orchestrator or direct input
    let (model, docs_obj) = if let Some(d) = documents {
        ("basic-rag".to_string(), d.to_object(py))
    } else {
        let routed_obj: PyObject = if let Some(o) = orchestrator {
            let kwargs = PyDict::new(py);
            kwargs.set_item("text_modality", false)?;
            kwargs.set_item("voice_modality", false)?;
            kwargs.set_item("music_modality", false)?;
            kwargs.set_item("documents", py.None())?;
            o.call_method("route", (text, emotion_data), Some(kwargs))?
                .to_object(py)
        } else {
            let orch = MoGEOrchestrator::new();
            let routed = orch.route(
                py,
                text,
                emotion_data,
                None,
                false,
                false,
                false,
                None,
                None,
            )?;
            routed.into_py(py)
        };

        let routed_dict: &PyDict = routed_obj
            .downcast(py)
            .map_err(|_| PyValueError::new_err("orchestrator must return a dict"))?;

        let model: String = routed_dict
            .get_item("model")?
            .ok_or_else(|| PyValueError::new_err("missing model from orchestrator"))?
            .extract()
            .map_err(|_| PyValueError::new_err("model must be a string"))?;

        let docs_obj = routed_dict
            .get_item("documents")?
            .map_or(py.None(), |o| o.to_object(py));

        (model, docs_obj)
    };

    // optional validator check
    if let Some(v) = validator {
        let res: &PyDict = v
            .call_method1("validate_action", ("operator", text))?
            .downcast()?;
        let compliant: bool = res
            .get_item("compliant")?
            .and_then(|o| o.extract().ok())
            .unwrap_or(true);
        if !compliant {
            return Err(PyValueError::new_err("validation failed"));
        }
    }

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
    let semantic = insight_semantics(text);

    let emotion: String = emotion_data
        .get_item("emotion")?
        .and_then(|o| o.extract().ok())
        .unwrap_or_else(|| "neutral".to_string());
    let opts = decide_expression_options(&emotion);

    let result = PyDict::new(py);
    result.set_item("model", model)?;
    result.set_item("tts_backend", opts.tts_backend)?;
    result.set_item("avatar_style", opts.avatar_style)?;
    result.set_item("aura", opts.aura)?;
    result.set_item("documents", docs_obj)?;
    result.set_item("memory", mem)?;
    result.set_item("core", core_output)?;
    result.set_item("insight_words", words)?;
    result.set_item("insight_bigrams", bigrams)?;
    result.set_item("insight_embedding", embedding)?;
    result.set_item("insight_semantic", semantic)?;
    result.set_item("latency_seconds", start.elapsed().as_secs_f64())?;
    Ok(result.into())
}

#[pyfunction]
pub fn route_inevitability(py: Python<'_>, expr: &str) -> PyResult<Py<PyDict>> {
    if expr.trim().is_empty() {
        return Err(PyValueError::new_err("expression cannot be empty"));
    }
    let (inevitability, journey) = reduce_inevitable_with_journey(expr);
    let result = PyDict::new(py);
    result.set_item("inevitability", inevitability)?;
    let journey_py: Vec<String> = journey.iter().map(|s| format!("{:?}", s)).collect();
    result.set_item("journey", journey_py)?;
    Ok(result.into())
}

#[pyfunction]
pub fn query_memory(py: Python<'_>, text: &str) -> PyResult<Py<PyDict>> {
    if text.trim().is_empty() {
        return Err(PyValueError::new_err("text cannot be empty"));
    }
    let mut bundle = MemoryBundle::new();
    bundle.initialize(py)?;
    bundle.query(py, text)
}

#[pyfunction]
pub fn insight_embedding(text: &str) -> PyResult<Vec<f32>> {
    Ok(insight_embed(text))
}

#[pyfunction]
pub fn insight_semantic(text: &str) -> PyResult<Vec<(String, f32)>> {
    Ok(insight_semantics(text))
}

#[pyfunction]
#[pyo3(
    signature = (
        integration,
        mission_path=None,
        persona_path=None,
        identity_path=None,
        extra_paths=None
    )
)]
pub fn load_identity(
    integration: &PyAny,
    mission_path: Option<&str>,
    persona_path: Option<&str>,
    identity_path: Option<&str>,
    extra_paths: Option<&PyAny>,
) -> PyResult<String> {
    let mission = mission_path.unwrap_or(MISSION_DOC);
    let persona = persona_path.unwrap_or(PERSONA_DOC);
    let identity = identity_path.unwrap_or(IDENTITY_FILE);
    let identity = PathBuf::from(identity);
    if identity.exists() {
        return Ok(fs::read_to_string(identity).map_err(|e| PyValueError::new_err(e.to_string()))?);
    }
    let mut sections: Vec<String> = Vec::new();

    let mission_path = PathBuf::from(mission);
    let persona_path = PathBuf::from(persona);

    let mission_text = fs::read_to_string(&mission_path).unwrap_or_default();
    if !mission_text.trim().is_empty() {
        sections.push(format!(
            "Mission Source ({}):\n{}",
            mission_path.display(),
            mission_text
        ));
    }

    let persona_text = fs::read_to_string(&persona_path).unwrap_or_default();
    if !persona_text.trim().is_empty() {
        sections.push(format!(
            "Persona Source ({}):\n{}",
            persona_path.display(),
            persona_text
        ));
    }

    let provided_paths: Vec<String> = if let Some(obj) = extra_paths {
        if obj.is_none() {
            Vec::new()
        } else {
            obj.extract::<Vec<String>>().map_err(|_| {
                PyValueError::new_err("extra_paths must be a sequence of strings")
            })?
        }
    } else {
        Vec::new()
    };

    let doctrine_paths: Vec<String> = if provided_paths.is_empty() {
        DOCTRINE_DOCS.iter().map(|p| p.to_string()).collect()
    } else {
        provided_paths
    };

    for path in doctrine_paths {
        let doctrine_path = PathBuf::from(&path);
        let doctrine_text = fs::read_to_string(&doctrine_path).unwrap_or_default();
        if doctrine_text.trim().is_empty() {
            continue;
        }
        sections.push(format!(
            "Doctrine Source ({}):\n{}",
            doctrine_path.display(),
            doctrine_text
        ));
    }

    let combined = sections.join("\n\n");
    let prompt = format!(
        "Summarize the mission, vision, persona, and doctrine inputs:\n{}",
        combined
    );
    let summary: String = integration.call_method1("complete", (prompt,))?.extract()?;
    if let Some(parent) = identity.parent() {
        fs::create_dir_all(parent).map_err(|e| PyValueError::new_err(e.to_string()))?;
    }
    fs::write(&identity, &summary).map_err(|e| PyValueError::new_err(e.to_string()))?;
    let _ = insight_analyze(&summary);
    Ok(summary)
}

#[pyfunction]
pub fn health_pulse() {
    emit_pulse("crown", true);
}

#[pymodule]
fn neoabzu_crown(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(route_query, m)?)?;
    m.add_function(wrap_pyfunction!(route_decision, m)?)?;
    m.add_function(wrap_pyfunction!(route_inevitability, m)?)?;
    m.add_function(wrap_pyfunction!(query_memory, m)?)?;
    m.add_function(wrap_pyfunction!(insight_embedding, m)?)?;
    m.add_function(wrap_pyfunction!(insight_semantic, m)?)?;
    m.add_function(wrap_pyfunction!(load_identity, m)?)?;
    m.add_function(wrap_pyfunction!(health_pulse, m)?)?;
    let _ = py; // reserve for future use
    Ok(())
}
