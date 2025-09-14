use neoabzu_rag::merge_documents;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyModule};

#[test]
fn combines_memory_and_connector_lists() {
    Python::with_gil(|py| {
        let mem_doc = PyDict::new(py);
        mem_doc.set_item("text", "abc").unwrap();
        let memory = PyList::new(py, [mem_doc]);

        let conn_doc = PyDict::new(py);
        conn_doc.set_item("text", "ext").unwrap();
        let connectors = PyList::new(py, [conn_doc]);

        let merged = merge_documents(py, "abc", memory, Some(connectors), 2, None).unwrap();
        let texts: Vec<String> = merged
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
        assert!(texts.contains(&"abc".to_string()));
        assert!(texts.contains(&"ext".to_string()));
    });
}

#[test]
fn custom_ranker_orders_connector_first() {
    Python::with_gil(|py| {
        let mem_doc = PyDict::new(py);
        mem_doc.set_item("text", "abc").unwrap();
        let memory = PyList::new(py, [mem_doc]);

        let conn_doc = PyDict::new(py);
        conn_doc.set_item("text", "ext").unwrap();
        let connectors = PyList::new(py, [conn_doc]);

        let ranker_code = r#"
def ranker(q, docs):
    for d in docs:
        d['score'] = 1.0 if d['source'] == 'connector' else 0.0
    return sorted(docs, key=lambda x: x['score'], reverse=True)
"#;
        let ranker_mod = PyModule::from_code(py, ranker_code, "", "ranker").unwrap();
        let ranker = ranker_mod.getattr("ranker").unwrap();

        let merged = merge_documents(
            py,
            "abc",
            memory,
            Some(connectors),
            2,
            Some(ranker),
        )
        .unwrap();
        let first: &PyDict = merged[0].as_ref(py);
        let source: String = first
            .get_item("source")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(source, "connector");
    });
}
