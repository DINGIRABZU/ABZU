use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyModule};

#[test]
fn test_route_query_uses_rust_retriever() {
    Python::with_gil(|py| {
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
     return [{'text':'abc'}]
"#;
        let vector_mod = PyModule::from_code(py, vector_code, "", "vector_memory").unwrap();
        modules.set_item("vector_memory", vector_mod).unwrap();

        let module = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = module.getattr("route_query").unwrap();
        let res: &PyList = func.call1(("hello", "Sage")).unwrap().downcast().unwrap();
        let first: &PyDict = res.get_item(0).unwrap().downcast().unwrap();
        let text: String = first.get_item("text").unwrap().unwrap().extract().unwrap();
        assert_eq!(text, "abc");
    });
}
