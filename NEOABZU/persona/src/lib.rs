use once_cell::sync::Lazy;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::sync::Mutex;

#[derive(Default)]
struct State {
    current_layer: Option<String>,
    last_emotion: Option<String>,
}

static STATE: Lazy<Mutex<State>> = Lazy::new(|| Mutex::new(State::default()));

#[pyfunction]
fn get_current_layer() -> PyResult<Option<String>> {
    Ok(STATE.lock().unwrap().current_layer.clone())
}

#[pyfunction]
fn set_current_layer(layer: Option<String>) -> PyResult<()> {
    STATE.lock().unwrap().current_layer = layer;
    Ok(())
}

#[pyfunction]
fn get_last_emotion() -> PyResult<Option<String>> {
    Ok(STATE.lock().unwrap().last_emotion.clone())
}

#[pyfunction]
fn set_last_emotion(emotion: Option<String>) -> PyResult<()> {
    STATE.lock().unwrap().last_emotion = emotion;
    Ok(())
}

#[derive(Deserialize)]
struct ProfilesFile {
    profiles: HashMap<String, HashMap<String, String>>,
}

#[pyfunction]
fn load_persona_profiles(py: Python<'_>, path: &str) -> PyResult<Py<PyDict>> {
    let text = fs::read_to_string(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    let data: ProfilesFile = serde_yaml::from_str(&text)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    let out = PyDict::new_bound(py);
    for (name, profile) in data.profiles {
        let entry = PyDict::new_bound(py);
        for (k, v) in profile {
            entry.set_item(k, v)?;
        }
        out.set_item(name, entry)?;
    }
    Ok(out.into())
}

#[pymodule]
fn neoabzu_persona(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_current_layer, m)?)?;
    m.add_function(wrap_pyfunction!(set_current_layer, m)?)?;
    m.add_function(wrap_pyfunction!(get_last_emotion, m)?)?;
    m.add_function(wrap_pyfunction!(set_last_emotion, m)?)?;
    m.add_function(wrap_pyfunction!(load_persona_profiles, m)?)?;
    Ok(())
}
