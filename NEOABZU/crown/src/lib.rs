use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

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
    if let Ok(hb_mod) = PyModule::import(py, "monitoring.chakra_heartbeat") {
        if let Ok(cls) = hb_mod.getattr("ChakraHeartbeat") {
            let hb = cls.call0()?;
            hb.call_method0("check_alerts")?;
            let status: String = hb.call_method0("sync_status")?.extract()?;
            if status != "Great Spiral" {
                if let Ok(bus) = PyModule::import(py, "agents.event_bus") {
                    let meta = PyDict::new(py);
                    meta.set_item("status", "out_of_sync")?;
                    let _ = bus
                        .getattr("emit_event")?
                        .call1(("chakra_heartbeat", "chakra_down", meta));
                }
                return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    "chakras out of sync",
                ));
            }
        }
    }

    let mut throughput: Option<PyObject> = None;
    let mut errors: Option<PyObject> = None;
    if let Ok(prom) = PyModule::import(py, "prometheus_client") {
        if let Ok(counter) = prom.getattr("Counter") {
            throughput = counter
                .call1((
                    "narrative_throughput_total",
                    "Narrative events processed",
                    ("service",),
                ))
                .ok()
                .map(|o| o.into_py(py));
            errors = counter
                .call1((
                    "service_errors_total",
                    "Number of errors encountered",
                    ("service",),
                ))
                .ok()
                .map(|o| o.into_py(py));
        }
    }
    if let Some(tc) = throughput.as_ref() {
        let _ = tc
            .as_ref(py)
            .call_method1("labels", ("crown",))
            .and_then(|l| l.call_method0("inc"));
    }

    let outcome = (|| -> PyResult<Py<PyDict>> {
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

        let result_obj = if std::env::var("INTERNAL_MODEL_PROTOCOL")
            .ok()
            .as_deref()
            == Some("mcp")
        {
            match PyModule::import(py, "mcp.gateway") {
                Ok(mcp) => {
                    let payload = PyDict::new(py);
                    payload.set_item("text", text)?;
                    payload.set_item("emotion_data", emotion_data)?;
                    payload.set_item("documents", &docs)?;
                    let json = PyModule::import(py, "json")?;
                    let payload_json = json.getattr("dumps")?.call1((payload,))?;
                    let invoke = mcp.getattr("invoke_model")?;
                    let asyncio = PyModule::import(py, "asyncio")?;
                    let coro = invoke.call1(("orchestrator_route", payload_json))?;
                    match asyncio.getattr("run")?.call1((coro,)) {
                        Ok(resp) => {
                            let any = resp
                                .get_item("result")
                                .unwrap_or_else(|_| PyDict::new(py).into());
                            any.into_py(py)
                        },
                        Err(_) => {
                            let kwargs = PyDict::new(py);
                            kwargs.set_item("text_modality", false)?;
                            kwargs.set_item("voice_modality", false)?;
                            kwargs.set_item("music_modality", false)?;
                            kwargs.set_item("documents", &docs)?;
                            orch_obj
                                .as_ref(py)
                                .call_method("route", (text, emotion_data), Some(kwargs))?
                                .into_py(py)
                        }
                    }
                }
                Err(_) => {
                    let kwargs = PyDict::new(py);
                    kwargs.set_item("text_modality", false)?;
                    kwargs.set_item("voice_modality", false)?;
                    kwargs.set_item("music_modality", false)?;
                    kwargs.set_item("documents", &docs)?;
                    orch_obj
                        .as_ref(py)
                        .call_method("route", (text, emotion_data), Some(kwargs))?
                        .into_py(py)
                }
            }
        } else {
            let kwargs = PyDict::new(py);
            kwargs.set_item("text_modality", false)?;
            kwargs.set_item("voice_modality", false)?;
            kwargs.set_item("music_modality", false)?;
            kwargs.set_item("documents", &docs)?;
            orch_obj
                .as_ref(py)
                .call_method("route", (text, emotion_data), Some(kwargs))?
                .into_py(py)
        };
        let result: &PyDict = result_obj.as_ref(py).downcast::<PyDict>()?;

        let emotion: String = emotion_data
            .get_item("emotion")?
            .and_then(|v| v.extract::<String>().ok())
            .unwrap_or_else(|| "neutral".to_string());

        let decider = PyModule::import(py, "crown_decider")?;
        let opts: &PyDict = decider
            .getattr("decide_expression_options")?
            .call1((&emotion,))?
            .downcast::<PyDict>()?;

        let soul_state: Option<String> = PyModule::import(py, "emotional_state")
            .ok()
            .and_then(|m| m.getattr("get_soul_state").ok())
            .and_then(|f| f.call0().ok())
            .and_then(|v| v.extract().ok());

        let (chakra_reg, records) = if let Ok(reg_mod) = PyModule::import(py, "memory.chakra_registry") {
            if let Ok(cls) = reg_mod.getattr("ChakraRegistry") {
                if let Ok(reg) = cls.call0() {
                    let kwargs = PyDict::new(py);
                    let filter = PyDict::new(py);
                    filter.set_item("type", "expression_decision")?;
                    filter.set_item("emotion", &emotion)?;
                    kwargs.set_item("filter", filter)?;
                    kwargs.set_item("k", 20)?;
                    let recs = reg
                        .call_method("search", ("crown", ""), Some(kwargs))
                        .ok();
                    (Some(reg.into_py(py)), recs)
                } else {
                    (None, None)
                }
            } else {
                (None, None)
            }
        } else {
            (None, None)
        };

        let mut backend_weights: HashMap<String, f64> = HashMap::new();
        if let Some(tts) = opts.get_item("tts_backend")? {
            backend_weights.insert(tts.extract()?, 1.0);
        }
        let mut avatar_weights: HashMap<String, f64> = HashMap::new();
        if let Some(style) = opts.get_item("avatar_style")? {
            avatar_weights.insert(style.extract()?, 1.0);
        }
        if let Some(recs) = records {
            for rec in recs.iter()? {
                let r: &PyDict = rec?.downcast()?;
                let weight = if let (Some(soul), Some(rec_soul)) = (
                    soul_state.as_ref(),
                    r.get_item("soul_state")?.and_then(|v| v.extract::<String>().ok()),
                ) {
                    if rec_soul == *soul { 2.0 } else { 1.0 }
                } else {
                    1.0
                };
                if let Ok(Some(b_any)) = r.get_item("tts_backend") {
                    if let Ok(b) = b_any.extract::<String>() {
                        *backend_weights.entry(b).or_insert(0.0) += weight;
                    }
                }
                if let Ok(Some(a_any)) = r.get_item("avatar_style") {
                    if let Ok(a) = a_any.extract::<String>() {
                        *avatar_weights.entry(a).or_insert(0.0) += weight;
                    }
                }
            }
        }

        let tts_backend = backend_weights
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(k, _)| k.clone())
            .unwrap_or_default();
        let avatar_style = avatar_weights
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(k, _)| k.clone())
            .unwrap_or_default();

        let rust_memory = PyModule::import(py, "memory.bundle")
            .and_then(|m| m.getattr("MemoryBundle"))
            .and_then(|c| c.call0())
            .and_then(|b| {
                b.call_method0("initialize")?;
                b.call_method1("query", (text,))
            })
            .ok();

        let core_output = PyModule::import(py, "neoabzu_core")
            .and_then(|m| m.getattr("evaluate_py"))
            .and_then(|f| f.call1((text,)))
            .ok();

        let decision = PyDict::new(py);
        if let Some(model) = result.get_item("model")? {
            decision.set_item("model", model)?;
        }
        decision.set_item("tts_backend", &tts_backend)?;
        decision.set_item("avatar_style", &avatar_style)?;
        if let Some(aura) = opts.get_item("aura")? {
            decision.set_item("aura", aura)?;
        }
        if let Some(mem) = rust_memory {
            decision.set_item("memory", mem)?;
        }
        if let Some(core) = core_output {
            decision.set_item("core", core)?;
        }
        if let Some(reg) = chakra_reg {
            let kwargs = PyDict::new(py);
            kwargs.set_item("type", "expression_decision")?;
            kwargs.set_item("emotion", &emotion)?;
            kwargs.set_item("tts_backend", &tts_backend)?;
            kwargs.set_item("avatar_style", &avatar_style)?;
            if let Some(soul) = soul_state {
                kwargs.set_item("soul_state", soul)?;
            }
            let _ = reg
                .as_ref(py)
                .call_method("record", ("crown", text, "crown_router"), Some(kwargs));
        }

        Ok(decision.into_py(py))
    })();

    if outcome.is_err() {
        if let Some(ec) = errors {
            let _ = ec
                .as_ref(py)
                .call_method1("labels", ("crown",))
                .and_then(|l| l.call_method0("inc"));
        }
    }

    outcome
}

#[pyfunction]
fn route_inevitability(py: Python<'_>, expr: &str) -> PyResult<Py<PyDict>> {
    let core = PyModule::import(py, "neoabzu_core")?;
    let reduce = core.getattr("reduce_inevitable")?;
    let (inevitability, journey): (f32, Vec<String>) = reduce.call1((expr,))?.extract()?;

    let narrative = format!("{inevitability}:{journey:?}");
    let statuses = PyDict::new(py);
    statuses.set_item("narrative", narrative)?;
    let memory = PyModule::import(py, "neoabzu_memory")?;
    let broadcast = memory.getattr("broadcast_layer_event")?;
    broadcast.call1((statuses,))?;

    let result = PyDict::new(py);
    result.set_item("inevitability", inevitability)?;
    result.set_item("journey", journey)?;
    Ok(result.into_py(py))
}

#[pyfunction]
fn query_memory(py: Python<'_>, text: &str) -> PyResult<Py<PyDict>> {
    let memory = PyModule::import(py, "neoabzu_memory")?;
    let func = memory.getattr("query_memory")?;
    func.call1((text,))?.extract()
}

#[pymodule]
fn neoabzu_crown(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(route_query, m)?)?;
    m.add_function(wrap_pyfunction!(route_decision, m)?)?;
    m.add_function(wrap_pyfunction!(route_inevitability, m)?)?;
    m.add_function(wrap_pyfunction!(query_memory, m)?)?;
    PyModule::import(py, "neoabzu_memory")?;
    Ok(())
}
