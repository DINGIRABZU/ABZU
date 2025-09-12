use std::collections::HashMap;
use std::sync::Mutex;

use once_cell::sync::Lazy;
use pyo3::exceptions::PyModuleNotFoundError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

#[cfg(feature = "tracing")]
use tracing::info_span;

static LAYERS: &[&str] = &[
    "cortex",
    "vector",
    "spiral",
    "emotional",
    "mental",
    "spiritual",
    "narrative",
];

static LAYER_IMPORTS: Lazy<HashMap<&'static str, &'static str>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("cortex", "memory.cortex");
    m.insert("vector", "vector_memory");
    m.insert("spiral", "spiral_memory");
    m.insert("emotional", "memory.emotional");
    m.insert("mental", "memory.mental");
    m.insert("spiritual", "memory.spiritual");
    m.insert("narrative", "memory.narrative_engine");
    m
});

static LAYER_STATUSES: Lazy<Mutex<HashMap<String, String>>> =
    Lazy::new(|| Mutex::new(HashMap::new()));

#[pyclass]
pub struct MemoryBundle {
    statuses: HashMap<String, String>,
}

#[pymethods]
impl MemoryBundle {
    #[new]
    pub fn new() -> Self {
        Self {
            statuses: HashMap::new(),
        }
    }

    pub fn initialize(&mut self, py: Python<'_>) -> PyResult<HashMap<String, String>> {
        #[cfg(feature = "tracing")]
        let span = info_span!("memory.bundle.initialize");
        #[cfg(feature = "tracing")]
        let _guard = span.enter();

        let mut statuses: HashMap<String, String> = HashMap::new();

        for layer in LAYERS {
            let module_path = LAYER_IMPORTS
                .get(layer)
                .expect("layer import path missing");
            let status = match PyModule::import(py, *module_path) {
                Ok(_) => "ready",
                Err(err) => {
                    if err.is_instance_of::<PyModuleNotFoundError>(py) {
                        let optional_path = format!("memory.optional.{layer}");
                        match PyModule::import(py, optional_path.as_str()) {
                            Ok(_) => "skipped",
                            Err(_) => "error",
                        }
                    } else {
                        "error"
                    }
                }
            };
            statuses.insert((*layer).to_string(), status.to_string());
        }

        {
            let mut global = LAYER_STATUSES.lock().unwrap();
            global.extend(statuses.clone());
        }

        broadcast_layer_event(py, statuses.clone())?;
        self.statuses = statuses.clone();
        Ok(statuses)
    }

    pub fn query(&self, py: Python<'_>, text: &str) -> PyResult<Py<PyDict>> {
        #[cfg(feature = "tracing")]
        let span = info_span!("memory.bundle.query", query = text);
        #[cfg(feature = "tracing")]
        let _guard = span.enter();

        let mut failed_layers: Vec<&str> = Vec::new();

        let cortex_res = match query_cortex(py, text) {
            Ok(obj) => obj,
            Err(_) => {
                failed_layers.push("cortex");
                PyList::empty(py).into_py(py)
            }
        };

        let vector_res = match query_vector(py, text) {
            Ok(obj) => obj,
            Err(_) => {
                failed_layers.push("vector");
                PyList::empty(py).into_py(py)
            }
        };

        let spiral_res = match query_spiral(py, text) {
            Ok(obj) => obj,
            Err(_) => {
                failed_layers.push("spiral");
                py.None()
            }
        };

        let emotional_res = match query_emotional(py, text) {
            Ok(obj) => obj,
            Err(_) => {
                failed_layers.push("emotional");
                PyList::empty(py).into_py(py)
            }
        };

        let mental_res = match query_mental(py, text) {
            Ok(obj) => obj,
            Err(_) => {
                failed_layers.push("mental");
                PyList::empty(py).into_py(py)
            }
        };

        let spiritual_res = match query_spiritual(py, text) {
            Ok(obj) => obj,
            Err(_) => {
                failed_layers.push("spiritual");
                PyList::empty(py).into_py(py)
            }
        };

        let narrative_res = match query_narrative(py, text) {
            Ok(obj) => obj,
            Err(_) => {
                failed_layers.push("narrative");
                PyList::empty(py).into_py(py)
            }
        };

        let result = PyDict::new(py);
        result.set_item("cortex", cortex_res)?;
        result.set_item("vector", vector_res)?;
        result.set_item("spiral", spiral_res)?;
        result.set_item("emotional", emotional_res)?;
        result.set_item("mental", mental_res)?;
        result.set_item("spiritual", spiritual_res)?;
        result.set_item("narrative", narrative_res)?;
        result.set_item("failed_layers", PyList::new(py, failed_layers))?;
        Ok(result.into())
    }
}

fn query_cortex(py: Python<'_>, text: &str) -> PyResult<PyObject> {
    for module_name in ["memory.cortex", "memory.optional.cortex"].iter() {
        if let Ok(module) = PyModule::import(py, *module_name) {
            if let Ok(func) = module.getattr("query_spirals") {
                let kwargs = PyDict::new(py);
                kwargs.set_item("text", text)?;
                return func.call((), Some(kwargs)).map(|o| o.into_py(py));
            }
        }
    }
    Err(PyErr::new::<pyo3::exceptions::PyException, _>("cortex query failed"))
}

fn query_vector(py: Python<'_>, text: &str) -> PyResult<PyObject> {
    for module_name in ["vector_memory", "memory.optional.vector_memory"].iter() {
        if let Ok(module) = PyModule::import(py, *module_name) {
            if let Ok(func) = module.getattr("query_vectors") {
                let filter = PyDict::new(py);
                filter.set_item("text", text)?;
                let kwargs = PyDict::new(py);
                kwargs.set_item("filter", filter)?;
                return func.call((), Some(kwargs)).map(|o| o.into_py(py));
            }
        }
    }
    Err(PyErr::new::<pyo3::exceptions::PyException, _>("vector query failed"))
}

fn query_spiral(py: Python<'_>, text: &str) -> PyResult<PyObject> {
    for module_name in ["spiral_memory", "memory.optional.spiral_memory"].iter() {
        if let Ok(module) = PyModule::import(py, *module_name) {
            if let Ok(func) = module.getattr("spiral_recall") {
                return func.call1((text,)).map(|o| o.into_py(py));
            }
        }
    }
    Err(PyErr::new::<pyo3::exceptions::PyException, _>("spiral query failed"))
}

fn query_emotional(py: Python<'_>, _text: &str) -> PyResult<PyObject> {
    for module_name in ["memory.emotional", "memory.optional.emotional"].iter() {
        if let Ok(module) = PyModule::import(py, *module_name) {
            if let Ok(func) = module.getattr("fetch_emotion_history") {
                return func.call1((100,)).map(|o| o.into_py(py));
            }
        }
    }
    Err(PyErr::new::<pyo3::exceptions::PyException, _>("emotional query failed"))
}

fn query_mental(py: Python<'_>, text: &str) -> PyResult<PyObject> {
    for module_name in ["memory.mental", "memory.optional.mental"].iter() {
        if let Ok(module) = PyModule::import(py, *module_name) {
            if let Ok(func) = module.getattr("query_related_tasks") {
                return func.call1((text,)).map(|o| o.into_py(py));
            }
        }
    }
    Err(PyErr::new::<pyo3::exceptions::PyException, _>("mental query failed"))
}

fn query_spiritual(py: Python<'_>, text: &str) -> PyResult<PyObject> {
    for module_name in ["memory.spiritual", "memory.optional.spiritual"].iter() {
        if let Ok(module) = PyModule::import(py, *module_name) {
            if let Ok(func) = module.getattr("lookup_symbol_history") {
                return func.call1((text,)).map(|o| o.into_py(py));
            }
        }
    }
    Err(PyErr::new::<pyo3::exceptions::PyException, _>("spiritual query failed"))
}

fn query_narrative(py: Python<'_>, _text: &str) -> PyResult<PyObject> {
    for module_name in [
        "memory.narrative_engine",
        "memory.optional.narrative_engine",
    ]
    .iter()
    {
        if let Ok(module) = PyModule::import(py, *module_name) {
            if let Ok(func) = module.getattr("stream_stories") {
                let iter = func.call0()?;
                let builtins = PyModule::import(py, "builtins")?;
                let list_obj = builtins.getattr("list")?.call1((iter,))?;
                return Ok(list_obj.into_py(py));
            }
        }
    }
    Err(PyErr::new::<pyo3::exceptions::PyException, _>("narrative query failed"))
}

#[pyfunction]
pub fn broadcast_layer_event(
    py: Python<'_>,
    mut statuses: HashMap<String, String>,
) -> PyResult<HashMap<String, String>> {
    {
        let mut global = LAYER_STATUSES.lock().unwrap();
        for layer in LAYERS {
            if let Some(status) = statuses.get(*layer) {
                global.insert((*layer).to_string(), status.clone());
            }
        }
    }

    for layer in LAYERS {
        if statuses.get(*layer).map(|s| s != "ready").unwrap_or(true) {
            let global = LAYER_STATUSES.lock().unwrap();
            let status = global
                .get(*layer)
                .cloned()
                .unwrap_or_else(|| "error".to_string());
            drop(global);
            statuses.entry((*layer).to_string()).or_insert(status);
        }
    }

    let event_bus = PyModule::import(py, "agents.event_bus")?;
    let emit_event = event_bus.getattr("emit_event")?;
    let layers = PyDict::new(py);
    for layer in LAYERS {
        layers.set_item(*layer, statuses.get(*layer).unwrap().as_str())?;
    }
    let payload = PyDict::new(py);
    payload.set_item("layers", layers)?;
    emit_event.call1(("memory", "layer_init", payload))?;
    Ok(statuses)
}

#[pyfunction]
pub fn query_memory(py: Python<'_>, text: &str) -> PyResult<Py<PyDict>> {
    let bundle = MemoryBundle::new();
    bundle.query(py, text)
}

#[pymodule]
fn neoabzu_memory(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<MemoryBundle>()?;
    m.add_function(wrap_pyfunction!(query_memory, m)?)?;
    m.add_function(wrap_pyfunction!(broadcast_layer_event, m)?)?;
    Ok(())
}
