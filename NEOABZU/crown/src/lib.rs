use neoabzu_insight::analyze as insight_analyze;
use neoabzu_memory::MemoryBundle;
use neoabzu_rag::{retrieve_top, MoGEOrchestrator};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};
use std::collections::HashMap;
use std::time::Instant;

fn get_tracer(py: Python<'_>) -> Option<PyObject> {
    PyModule::import(py, "opentelemetry.trace")
        .and_then(|m| m.getattr("get_tracer"))
        .and_then(|f| f.call1(("crown",)))
        .map(|t| t.into_py(py))
        .ok()
}

fn get_bundle(py: Python<'_>) -> PyResult<Py<MemoryBundle>> {
    let bundle = Py::new(py, MemoryBundle::new())?;
    bundle.borrow_mut(py).initialize(py)?;
    Ok(bundle)
}

fn get_core_eval(py: Python<'_>) -> PyResult<PyObject> {
    let memory = PyModule::import(py, "neoabzu_memory")?;
    Ok(memory.getattr("eval_core")?.into_py(py))
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
    let _store = select_store(archetype);
    let res = retrieve_top(py, question, 5, None)?;
    Ok(PyList::new(py, res).into_py(py))
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
    // setup counters
    let (throughput_counter, error_counter) = if let Ok(prom) = PyModule::import(py, "prometheus_client") {
        if let (Ok(registry), Ok(counter_cls)) = (prom.getattr("REGISTRY"), prom.getattr("Counter")) {
            if let Ok(collectors) = registry.getattr("_names_to_collectors") {
                let tp = match collectors.get_item("narrative_throughput_total") {
                    Ok(o) => o.to_object(py),
                    Err(_) => counter_cls
                        .call((
                            "narrative_throughput_total",
                            "Narrative events processed",
                            vec!["service"],
                        ), None)
                        .unwrap()
                        .into_py(py),
                };
                let err = match collectors.get_item("service_errors_total") {
                    Ok(o) => o.to_object(py),
                    Err(_) => counter_cls
                        .call((
                            "service_errors_total",
                            "Number of errors encountered",
                            vec!["service"],
                        ), None)
                        .unwrap()
                        .into_py(py),
                };
                (Some(tp), Some(err))
            } else {
                (None, None)
            }
        } else {
            (None, None)
        }
    } else {
        (None, None)
    };
    if let Some(ref tp) = throughput_counter {
        let _ = tp
            .as_ref(py)
            .call_method("labels", ("crown",), None)
            .and_then(|l| l.call_method0("inc"));
    }

    let result: PyResult<Py<PyDict>> = (|| {
        if let Ok(hb_mod) = PyModule::import(py, "monitoring.chakra_heartbeat") {
            if let (Ok(cls), Ok(bus)) = (
                hb_mod.getattr("ChakraHeartbeat"),
                PyModule::import(py, "agents.event_bus"),
            ) {
                if let Ok(hb) = cls.call0() {
                    let _ = hb.call_method0("check_alerts");
                    if let Ok(status) = hb
                        .call_method0("sync_status")
                        .and_then(|v| v.extract::<String>())
                    {
                        if status != "Great Spiral" {
                            if let Ok(emit) = bus.getattr("emit_event") {
                                let payload = PyDict::new(py);
                                payload.set_item("status", "out_of_sync")?;
                                let _ = emit.call1(("chakra_heartbeat", "chakra_down", payload));
                            }
                            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                "chakras out of sync",
                            ));
                        }
                    }
                }
            }
        }

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

        let mut rust_memory: Option<PyObject> = None;
        let mut core_output: Option<PyObject> = None;
        let docs = match documents {
            Some(d) => d,
            None => {
                if let Some(ref tracer) = tracer {
                    let span = tracer.as_ref(py).call_method(
                        "start_as_current_span",
                        ("memory_bundle",),
                        None,
                    )?;
                    let _ = span.call_method0("__enter__")?;
                    let bundle = get_bundle(py)?;
                    let eval = get_core_eval(py)?;
                    core_output = eval.call1(py, (text,)).ok();
                    let corpus = bundle.borrow(py).query(py, text);
                    rust_memory = corpus.as_ref().ok().map(|c| c.into_py(py));
                    let _ = span.call_method(
                        "__exit__",
                        (py.None(), py.None(), py.None()),
                        None,
                    )?;
                    rust_memory.clone().unwrap_or_else(|| py.None().into_py(py))
                } else {
                    let bundle = get_bundle(py)?;
                    let eval = get_core_eval(py)?;
                    core_output = eval.call1(py, (text,)).ok();
                    let query = bundle.borrow(py).query(py, text)?;
                    rust_memory = Some(query.clone_ref(py).into_py(py));
                    query.into_py(py)
                }
            }
        };

        let orch_obj = match orchestrator {
            Some(o) => o,
            None => Py::new(py, MoGEOrchestrator::new())?.into_py(py),
        };

        let kwargs = PyDict::new(py);
        kwargs.set_item("text_modality", false)?;
        kwargs.set_item("voice_modality", false)?;
        kwargs.set_item("music_modality", false)?;
        kwargs.set_item("documents", docs.clone_ref(py))?;
        let result_obj = if let Some(ref tracer) = tracer {
            let span = tracer.as_ref(py).call_method(
                "start_as_current_span",
                ("core_evaluation",),
                None,
            )?;
            let _ = span.call_method0("__enter__")?;
            let res = orch_obj
                .as_ref(py)
                .call_method("route", (text, emotion_data), Some(kwargs));
            let _ = span.call_method("__exit__", (py.None(), py.None(), py.None()), None)?;
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
        if let Some(mem) = rust_memory {
            decision.set_item("memory", mem)?;
        }
        if let Some(core) = core_output {
            decision.set_item("core", core)?;
        }
        if let Ok(reason_mod) = PyModule::import(py, "neoabzu_insight") {
            if let Ok(f) = reason_mod.getattr("reason") {
                if let Ok(val) = f.call1((text,)) {
                    decision.set_item("insight", val)?;
                }
            }
        }
        let duration = start.elapsed().as_secs_f64();
        if let Ok(prometheus) = PyModule::import(py, "prometheus_client") {
            if let (Ok(registry), Ok(hist_cls), Ok(gauge_cls)) = (
                prometheus.getattr("REGISTRY"),
                prometheus.getattr("Histogram"),
                prometheus.getattr("Gauge"),
            ) {
                if let Ok(collectors) = registry.getattr("_names_to_collectors") {
                    let latency_hist = match collectors
                        .get_item("service_request_latency_seconds")
                    {
                        Ok(o) => o.to_object(py),
                        Err(_) => hist_cls
                            .call((
                                "service_request_latency_seconds",
                                "Request latency in seconds",
                                vec!["service"],
                            ), None)
                            .unwrap()
                            .into_py(py),
                    };
                    let _ = latency_hist
                        .as_ref(py)
                        .call_method("labels", ("crown",), None)
                        .and_then(|l| l.call_method("observe", (duration,), None));

                    let cpu_gauge = match collectors.get_item("service_cpu_usage_percent") {
                        Ok(o) => o.to_object(py),
                        Err(_) => gauge_cls
                            .call((
                                "service_cpu_usage_percent",
                                "CPU usage percent",
                                vec!["service"],
                            ), None)
                            .unwrap()
                            .into_py(py),
                    };
                    let memory_gauge = match collectors.get_item("service_memory_usage_bytes") {
                        Ok(o) => o.to_object(py),
                        Err(_) => gauge_cls
                            .call((
                                "service_memory_usage_bytes",
                                "Memory usage in bytes",
                                vec!["service"],
                            ), None)
                            .unwrap()
                            .into_py(py),
                    };
                    let gpu_gauge = match collectors.get_item("service_gpu_memory_usage_bytes") {
                        Ok(o) => o.to_object(py),
                        Err(_) => gauge_cls
                            .call((
                                "service_gpu_memory_usage_bytes",
                                "GPU memory usage in bytes",
                                vec!["service"],
                            ), None)
                            .unwrap()
                            .into_py(py),
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
                                if let Ok(used) = mem_info.getattr("used").and_then(|v| v.extract::<u64>()) {
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
    })();

    if result.is_err() {
        if let Some(ref err) = error_counter {
            let _ = err
                .as_ref(py)
                .call_method("labels", ("crown",), None)
                .and_then(|l| l.call_method0("inc"));
        }
    }
    result
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
                        .unwrap()
                        .into_py(py),
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
