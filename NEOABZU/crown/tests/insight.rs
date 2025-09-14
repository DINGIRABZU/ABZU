use neoabzu_crown::route_decision;
use pyo3::types::PyDict;
use pyo3::Python;

#[test]
fn exposes_insight_embedding() {
    Python::with_gil(|py| {
        let emo = PyDict::new(py);
        emo.set_item("emotion", "neutral").unwrap();
        let result = route_decision(py, "hello world", emo, None, None, None).unwrap();
        let emb: Vec<f32> = result
            .as_ref(py)
            .get_item("insight_embedding")
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(emb.len(), 3);
    });
}
