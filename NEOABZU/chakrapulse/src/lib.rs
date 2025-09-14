use once_cell::sync::Lazy;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use crossbeam_channel::{unbounded, Receiver, Sender};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[derive(Clone, Debug)]
pub struct Pulse {
    pub source: String,
    pub ok: bool,
    pub timestamp: u64,
}

static BUS: Lazy<Mutex<Vec<Sender<Pulse>>>> = Lazy::new(|| Mutex::new(Vec::new()));

pub fn emit_pulse(source: &str, ok: bool) {
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let pulse = Pulse {
        source: source.to_string(),
        ok,
        timestamp: ts,
    };
    let mut bus = BUS.lock().unwrap();
    bus.retain(|tx| tx.send(pulse.clone()).is_ok());
}

pub fn subscribe_chakra() -> Receiver<Pulse> {
    let (tx, rx) = unbounded();
    BUS.lock().unwrap().push(tx);
    rx
}

#[pyclass]
#[derive(Clone)]
struct PyPulse {
    #[pyo3(get)]
    source: String,
    #[pyo3(get)]
    ok: bool,
    #[pyo3(get)]
    timestamp: u64,
}

impl From<Pulse> for PyPulse {
    fn from(p: Pulse) -> Self {
        Self {
            source: p.source,
            ok: p.ok,
            timestamp: p.timestamp,
        }
    }
}

#[pyclass]
struct ChakraReceiver {
    rx: Receiver<Pulse>,
}

#[pymethods]
impl ChakraReceiver {
    fn recv(&self) -> Option<PyPulse> {
        self.rx.recv().ok().map(PyPulse::from)
    }
}

#[pyfunction]
fn emit_pulse_py(source: &str, ok: bool) {
    emit_pulse(source, ok);
}

#[pyfunction]
fn subscribe_chakra_py() -> ChakraReceiver {
    ChakraReceiver {
        rx: subscribe_chakra(),
    }
}

#[pymodule]
fn neoabzu_chakrapulse(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyPulse>()?;
    m.add_class::<ChakraReceiver>()?;
    m.add_function(wrap_pyfunction!(emit_pulse_py, m)?)?;
    m.add_function(wrap_pyfunction!(subscribe_chakra_py, m)?)?;
    Ok(())
}
