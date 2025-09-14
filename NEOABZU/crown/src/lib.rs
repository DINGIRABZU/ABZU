use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::time::Instant;

static TRACER: GILOnceCell<Option<PyObject>> = GILOnceCell::new();

fn get_tracer(py: Python<'_>) -> Option<PyObject> {
    TRACER
        .get_or_init(py, || {
            PyModule::import(py, "opentelemetry.trace")
                .and_then(|m| m.getattr("get_tracer"))
                .and_then(|f| f.call1(("crown",)))
                .map(|t| t.into_py(py))
                .ok()
        })
        .clone()
}

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
    let start = Instant::now();
    let tracer = get_tracer(py);
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
            if let Some(ref tracer) = tracer {
                let span = tracer.as_ref(py).call_method(
                    "start_as_current_span",
                    ("memory_bundle",),
                    None,
                )?;
                let _ = span.as_ref(py).call_method0("__enter__");
                let corpus = registry.call_method0("get_corpus");
                let _ = span.as_ref(py).call_method(
                    "__exit__",
                    (py.None(), py.None(), py.None()),
                    None,
                );
                corpus?.into_py(py)
            } else {
                registry.call_method0("get_corpus")?.into_py(py)
            }
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
    let result_obj = if let Some(ref tracer) = tracer {
        let span =
            tracer
                .as_ref(py)
                .call_method("start_as_current_span", ("core_evaluation",), None)?;
        let _ = span.as_ref(py).call_method0("__enter__");
        let res = orch_obj
            .as_ref(py)
            .call_method("route", (text, emotion_data), Some(kwargs));
        let _ = span
            .as_ref(py)
            .call_method("__exit__", (py.None(), py.None(), py.None()), None);
        res?
    } else {
        orch_obj
            .as_ref(py)
            .call_method("route", (text, emotion_data), Some(kwargs))?
    };
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
    let duration = start.elapsed().as_secs_f64();
    if let Ok(prometheus) = PyModule::import(py, "prometheus_client") {
        if let (Ok(registry), Ok(hist_cls), Ok(gauge_cls)) = (
            prometheus.getattr("REGISTRY"),
            prometheus.getattr("Histogram"),
            prometheus.getattr("Gauge"),
        ) {
            if let Ok(collectors) = registry.getattr("_names_to_collectors") {
                let latency_hist = match collectors.get_item("service_request_latency_seconds") {
                    Ok(o) => o.to_object(py),
                    Err(_) => hist_cls
                        .call(
                            (
                                "service_request_latency_seconds",
                                "Request latency in seconds",
                                vec!["service"],
                            ),
                            None,
                        )
                        .unwrap(),
                };
                let _ = latency_hist
                    .as_ref(py)
                    .call_method("labels", ("crown",), None)
                    .and_then(|l| l.call_method("observe", (duration,), None));

                let cpu_gauge = match collectors.get_item("service_cpu_usage_percent") {
                    Ok(o) => o.to_object(py),
                    Err(_) => gauge_cls
                        .call(
                            (
                                "service_cpu_usage_percent",
                                "CPU usage percent",
                                vec!["service"],
                            ),
                            None,
                        )
                        .unwrap(),
                };
                let memory_gauge = match collectors.get_item("service_memory_usage_bytes") {
                    Ok(o) => o.to_object(py),
                    Err(_) => gauge_cls
                        .call(
                            (
                                "service_memory_usage_bytes",
                                "Memory usage in bytes",
                                vec!["service"],
                            ),
                            None,
                        )
                        .unwrap(),
                };
                let gpu_gauge = match collectors.get_item("service_gpu_memory_usage_bytes") {
                    Ok(o) => o.to_object(py),
                    Err(_) => gauge_cls
                        .call(
                            (
                                "service_gpu_memory_usage_bytes",
                                "GPU memory usage in bytes",
                                vec!["service"],
                            ),
                            None,
                        )
                        .unwrap(),
                };

                if let Ok(psutil) = PyModule::import(py, "psutil") {
                    if let (Ok(cpu_percent), Ok(mem_used)) = (
                        psutil
                            .call_method0("cpu_percent")
                            .and_then(|v| v.extract::<f64>()),
                        psutil
                            .getattr("virtual_memory")
                            .and_then(|f| f.call0())
                            .and_then(|v| v.getattr("used"))
                            .and_then(|v| v.extract::<u64>()),
                    ) {
                        let _ = cpu_gauge
                            .as_ref(py)
                            .call_method("labels", ("crown",), None)
                            .and_then(|l| l.call_method("set", (cpu_percent,), None));
                        let _ = memory_gauge
                            .as_ref(py)
                            .call_method("labels", ("crown",), None)
                            .and_then(|l| l.call_method("set", (mem_used,), None));
                    }
                }

                if let Ok(pynvml) = PyModule::import(py, "pynvml") {
                    let _ = pynvml.call_method0("nvmlInit");
                    if let Ok(handle) = pynvml.call_method1("nvmlDeviceGetHandleByIndex", (0,)) {
                        if let Ok(mem_info) =
                            pynvml.call_method1("nvmlDeviceGetMemoryInfo", (handle.clone(),))
                        {
                            if let Ok(used) =
                                mem_info.getattr("used").and_then(|v| v.extract::<u64>())
                            {
                                let _ = gpu_gauge
                                    .as_ref(py)
                                    .call_method("labels", ("crown",), None)
                                    .and_then(|l| l.call_method("set", (used,), None));
                            }
                        }
                    }
                }
            }
        }
    }
    Ok(decision.into_py(py))
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
    let start = Instant::now();
    m.add_function(wrap_pyfunction!(route_query, m)?)?;
    m.add_function(wrap_pyfunction!(route_decision, m)?)?;
    m.add_function(wrap_pyfunction!(route_inevitability, m)?)?;
    m.add_function(wrap_pyfunction!(query_memory, m)?)?;
    PyModule::import(py, "neoabzu_memory")?;
    let duration = start.elapsed().as_secs_f64();
    if let Ok(prometheus) = PyModule::import(py, "prometheus_client") {
        if let (Ok(registry), Ok(gauge_cls)) =
            (prometheus.getattr("REGISTRY"), prometheus.getattr("Gauge"))
        {
            if let Ok(collectors) = registry.getattr("_names_to_collectors") {
                let boot_gauge = match collectors.get_item("service_boot_duration_seconds") {
                    Ok(o) => o.to_object(py),
                    Err(_) => gauge_cls
                        .call(
                            (
                                "service_boot_duration_seconds",
                                "Service boot duration in seconds",
                                vec!["service"],
                            ),
                            None,
                        )
                        .unwrap(),
                };
                let _ = boot_gauge
                    .as_ref(py)
                    .call_method("labels", ("crown",), None)
                    .and_then(|l| l.call_method("set", (duration,), None));
            }
        }
    }
    Ok(())
}
