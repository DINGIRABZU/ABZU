use neoabzu_rag::{retrieve_top, CosineRanker, FuncConnector};
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
fn plugin_connector_and_ranker() {
    Python::with_gil(|py| {
        setup(py);
        let conn_code = r#"
def fetch(q):
    return [{'text': 'external'}]
"#;
        let conn_mod = PyModule::from_code(py, conn_code, "", "connector").unwrap();
        let fetch = conn_mod.getattr("fetch").unwrap();
        let wrapper = Py::new(py, FuncConnector::new(fetch.into())).unwrap();
        let connectors = PyList::new(py, [wrapper.into_py(py)]);

        let ranker = Py::new(py, CosineRanker::new()).unwrap();
        let res = retrieve_top(py, "abc", 2, Some(connectors), Some(ranker.as_ref(py))).unwrap();

        let first: &PyDict = res[0].as_ref(py);
        let text: String = first.get_item("text").unwrap().unwrap().extract().unwrap();
        assert_eq!(text, "abc");

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
    });
}
