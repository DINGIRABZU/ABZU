use pyo3::prelude::*;
use pyo3::types::PyDict;

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
    let store = select_store(archetype);
    let retriever = PyModule::import(py, "rag.retriever")?;
    let func = retriever.getattr("retrieve_top")?;
    let kwargs = PyDict::new(py);
    kwargs.set_item("collection", store)?;
    func.call((question,), Some(kwargs)).map(|o| o.into_py(py))
}

#[pyfunction]
#[pyo3(signature = (text, emotion_data, orchestrator=None, validator=None, documents=None))]
fn route_decision(
    py: Python<'_>,
    text: &str,
    emotion_data: &PyDict,
    orchestrator: Option<PyObject>,
    validator: Option<PyObject>,
    documents: Option<PyObject>,
) -> PyResult<Py<PyDict>> {
    if let Some(val) = validator {
        let res = val
            .as_ref(py)
            .call_method("validate_action", ("crown", text), None)?;
        let compliant = res
            .get_item("compliant")
            .and_then(|v| v.extract::<bool>())
            .unwrap_or(false);
        if !compliant {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "ethical violation",
            ));
        }
    }

    let docs = match documents {
        Some(d) => d,
        None => {
            let module = PyModule::import(py, "agents.nazarick.document_registry")?;
            let cls = module.getattr("DocumentRegistry")?;
            let registry = cls.call0()?;
            registry.call_method0("get_corpus")?.into_py(py)
        }
    };

    let orch_obj = match orchestrator {
        Some(o) => o,
        None => {
            let module = PyModule::import(py, "rag.orchestrator")?;
            let cls = module.getattr("MoGEOrchestrator")?;
            cls.call0()?.into_py(py)
        }
    };

    let kwargs = PyDict::new(py);
    kwargs.set_item("text_modality", false)?;
    kwargs.set_item("voice_modality", false)?;
    kwargs.set_item("music_modality", false)?;
    kwargs.set_item("documents", docs)?;
    let result_obj = orch_obj
        .as_ref(py)
        .call_method("route", (text, emotion_data), Some(kwargs))?;
    let result: &PyDict = result_obj.downcast::<PyDict>()?;

    let emotion = emotion_data.get_item("emotion").ok().flatten();
    let none = py.None();
    let emotion = match emotion {
        Some(v) => v,
        None => none.as_ref(py),
    };
    let decider = PyModule::import(py, "crown_decider")?;
    let opts: &PyDict = decider
        .getattr("decide_expression_options")?
        .call1((emotion,))?
        .downcast::<PyDict>()?;
    let decision = PyDict::new(py);
    if let Some(model) = result.get_item("model")? {
        decision.set_item("model", model)?;
    }
    if let Some(tts) = opts.get_item("tts_backend")? {
        decision.set_item("tts_backend", tts)?;
    }
    if let Some(style) = opts.get_item("avatar_style")? {
        decision.set_item("avatar_style", style)?;
    }
    if let Some(aura) = opts.get_item("aura")? {
        decision.set_item("aura", aura)?;
    }
    Ok(decision.into_py(py))
}

#[pymodule]
fn neoabzu_crown(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(route_query, m)?)?;
    m.add_function(wrap_pyfunction!(route_decision, m)?)?;
    Ok(())
}
