use pyo3::prelude::*;

#[test]
fn test_route_query_selects_store() {
    Python::with_gil(|py| {
        py.run(
            r#"
import types, sys
called = {}

def fake_retrieve(q, top_n=5, collection="tech"):
    called['store'] = collection
    return []

retriever = types.ModuleType('retriever')
retriever.retrieve_top = fake_retrieve
rag = types.ModuleType('rag')
rag.retriever = retriever
sys.modules['rag'] = rag
sys.modules['rag.retriever'] = retriever
"#,
            None,
            None,
        )
        .unwrap();

        let module = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = module.getattr("route_query").unwrap();
        func.call1(("hello", "Sage")).unwrap();
        let store: String = py
            .eval("called['store']", None, None)
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(store, "tech");

        func.call1(("hello", "Jester")).unwrap();
        let store: String = py
            .eval("called['store']", None, None)
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(store, "music");
    });
}
