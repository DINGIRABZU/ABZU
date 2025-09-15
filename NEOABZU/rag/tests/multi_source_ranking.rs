use neoabzu_rag::MoGEOrchestrator;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyModule};

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
    return [{'text':'mem'}]
"#;
    let vector_mod = PyModule::from_code(py, vector_code, "", "vector_memory").unwrap();
    modules.set_item("vector_memory", vector_mod).unwrap();
}

#[test]
fn ranks_across_multiple_sources() {
    Python::with_gil(|py| {
        setup(py);
        let conn1_code = r#"
def fetch(q):
    return [{'text': 'alpha'}]
"#;
        let conn2_code = r#"
def fetch(q):
    return [{'text': 'beta'}]
"#;
        let mod1 = PyModule::from_code(py, conn1_code, "", "conn1").unwrap();
        let mod2 = PyModule::from_code(py, conn2_code, "", "conn2").unwrap();
        let connectors = PyList::new(py, [mod1.getattr("fetch").unwrap(), mod2.getattr("fetch").unwrap()]);
        let orch = MoGEOrchestrator::new();
        let emotion = PyDict::new(py);
        let kwargs = PyDict::new(py);
        kwargs.set_item("connectors", connectors).unwrap();
        let result = orch
            .route(
                py,
                "alpha",
                emotion,
                None,
                true,
                false,
                false,
                None,
                Some(kwargs),
            )
            .unwrap();
        let docs_any = result.as_ref(py).get_item("documents").unwrap().unwrap();
        let docs: &PyList = docs_any.downcast().unwrap();
        assert_eq!(docs.len(), 3);
        let texts: Vec<String> = docs
            .iter()
            .map(|d| {
                d.downcast::<PyDict>()
                    .unwrap()
                    .get_item("text")
                    .unwrap()
                    .unwrap()
                    .extract()
                    .unwrap()
            })
            .collect();
        assert!(texts.contains(&"mem".to_string()));
        assert!(texts.contains(&"alpha".to_string()));
        assert!(texts.contains(&"beta".to_string()));
        let first: &PyDict = docs[0].downcast().unwrap();
        let first_text: String = first
            .get_item("text")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(first_text, "alpha");
    });
}
