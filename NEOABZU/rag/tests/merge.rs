use neoabzu_rag::merge_documents;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

#[test]
fn combines_memory_and_connector_lists() {
    Python::with_gil(|py| {
        let mem_doc = PyDict::new(py);
        mem_doc.set_item("text", "abc").unwrap();
        let memory = PyList::new(py, [mem_doc]);

        let conn_doc = PyDict::new(py);
        conn_doc.set_item("text", "ext").unwrap();
        let connectors = PyList::new(py, [conn_doc]);

        let merged = merge_documents(py, "abc", memory, Some(connectors), 2).unwrap();
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
