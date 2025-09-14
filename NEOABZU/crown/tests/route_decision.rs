use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn route_decision_returns_documents() {
    Python::with_gil(|py| {
        let module = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = module.getattr("route_decision").unwrap();
        let emotion = PyDict::new(py);
        emotion.set_item("emotion", "joy").unwrap();
        let docs = PyDict::new(py);
        docs.set_item("doc", "value").unwrap();
        let kwargs = PyDict::new(py);
        kwargs.set_item("documents", docs).unwrap();
        let res: &PyDict = func
            .call(("hi", emotion, py.None(), py.None()), Some(kwargs))
            .unwrap()
            .downcast()
            .unwrap();
        let model: String = res.get_item("model").unwrap().unwrap().extract().unwrap();
        assert_eq!(model, "basic-rag");
        let docs_out: &PyDict = res.get_item("documents").unwrap().unwrap().downcast().unwrap();
        let doc_val: String = docs_out.get_item("doc").unwrap().unwrap().extract().unwrap();
        assert_eq!(doc_val, "value");
    });
}
