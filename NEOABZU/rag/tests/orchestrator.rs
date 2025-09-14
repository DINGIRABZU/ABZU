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
    return [{'text':'abc'}]
"#;
    let vector_mod = PyModule::from_code(py, vector_code, "", "vector_memory").unwrap();
    modules.set_item("vector_memory", vector_mod).unwrap();
}

#[test]
fn aggregates_memory_and_connector_results() {
    Python::with_gil(|py| {
        setup(py);
        let conn_code = r#"
def fetch(q):
    return [{'text': 'ext'}]
"#;
        let conn_mod = PyModule::from_code(py, conn_code, "", "connector").unwrap();
        let fetch = conn_mod.getattr("fetch").unwrap();
        let connectors = PyList::new(py, [fetch]);
        let orchestrator = MoGEOrchestrator::new();
        let emotion = PyDict::new(py);
        let kwargs = PyDict::new(py);
        kwargs.set_item("connectors", connectors).unwrap();
        let result = orchestrator
            .route(
                py,
                "abc",
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
        assert!(texts.contains(&"abc".to_string()));
        assert!(texts.contains(&"ext".to_string()));
    });
}

#[test]
fn route_uses_custom_ranker() {
    Python::with_gil(|py| {
        setup(py);
        let conn_code = r#"
def fetch(q):
    return [{'text': 'ext'}]
"#;
        let conn_mod = PyModule::from_code(py, conn_code, "", "connector").unwrap();
        let fetch = conn_mod.getattr("fetch").unwrap();
        let connectors = PyList::new(py, [fetch]);
        let ranker_code = r#"
def ranker(q, docs):
    for d in docs:
        d['score'] = 1.0 if d['source'] == 'connector' else 0.0
    return sorted(docs, key=lambda x: x['score'], reverse=True)
"#;
        let ranker_mod = PyModule::from_code(py, ranker_code, "", "ranker").unwrap();
        let ranker = ranker_mod.getattr("ranker").unwrap();
        let orchestrator = MoGEOrchestrator::new();
        let emotion = PyDict::new(py);
        let kwargs = PyDict::new(py);
        kwargs.set_item("connectors", connectors).unwrap();
        kwargs.set_item("ranker", ranker).unwrap();
        let result = orchestrator
            .route(
                py,
                "abc",
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
        let first: &PyDict = docs[0].downcast().unwrap();
        let source: String = first
            .get_item("source")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(source, "connector");
    });
}
