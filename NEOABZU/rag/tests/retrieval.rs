use neoabzu_rag::retrieve_top;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule};

fn setup(py: Python<'_>) {
    let sys = py.import("sys").unwrap();
    let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();
    let agents = PyModule::new(py, "agents").unwrap();
    modules.set_item("agents", agents).unwrap();
    let event_code = r#"
events = []

def emit_event(actor, action, metadata):
    events.append((actor, action, metadata))
"#;
    let event_bus = PyModule::from_code(py, event_code, "", "event_bus").unwrap();
    modules.set_item("agents.event_bus", event_bus).unwrap();
    let vector_code = r#"
def query_vectors(*a, **k):
    return [{'text':'abc'},{'text':'zzz'}]
"#;
    let vector_mod = PyModule::from_code(py, vector_code, "", "vector_memory").unwrap();
    modules.set_item("vector_memory", vector_mod).unwrap();
}

#[test]
fn ranks_vectors() {
    Python::with_gil(|py| {
        setup(py);
        let res = retrieve_top(py, "abc", 1).unwrap();
        let first: &PyDict = res[0].as_ref(py);
        let text: String = first
            .get_item("text")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(text, "abc");
    });
}

