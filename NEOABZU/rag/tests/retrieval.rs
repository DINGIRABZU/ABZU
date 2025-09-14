use neoabzu_rag::retrieve_top;
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
    return [{'text':'abc'},{'text':'zzz'}]
"#;
    let vector_mod = PyModule::from_code(py, vector_code, "", "vector_memory").unwrap();
    modules.set_item("vector_memory", vector_mod).unwrap();
}

#[test]
fn ranks_vectors() {
    Python::with_gil(|py| {
        setup(py);
        let res = retrieve_top(py, "abc", 1, None, None).unwrap();
        let first: &PyDict = res[0].as_ref(py);
        let text: String = first.get_item("text").unwrap().unwrap().extract().unwrap();
        assert_eq!(text, "abc");
    });
}

#[test]
fn merges_connector_results() {
    Python::with_gil(|py| {
        setup(py);
        let conn_code = r#"
def fetch(q):
    return [{'text': 'external'}]
"#;
        let conn_mod = PyModule::from_code(py, conn_code, "", "connector").unwrap();
        let fetch = conn_mod.getattr("fetch").unwrap();
        let connectors = PyList::new(py, [fetch]);
        let res = retrieve_top(py, "abc", 3, Some(connectors), None).unwrap();
        let texts: Vec<String> = res
            .iter()
            .map(|d| {
                d.as_ref(py)
                    .get_item("text")
                    .unwrap()
                    .unwrap()
                    .extract()
                    .unwrap()
            })
            .collect();
        assert!(texts.contains(&"external".to_string()));
        assert!(texts.contains(&"abc".to_string()));
    });
}

#[test]
fn custom_ranker_prioritizes_connector() {
    Python::with_gil(|py| {
        setup(py);
        let conn_code = r#"
def fetch(q):
    return [{'text': 'external'}]
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

        let res = retrieve_top(py, "abc", 2, Some(connectors), Some(ranker)).unwrap();
        let first: &PyDict = res[0].as_ref(py);
        let source: String = first
            .get_item("source")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(source, "connector");
    });
}
