use neoabzu_insight::crown_semantic;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule};

#[test]
fn crown_semantic_returns_python_bridge_output() {
    Python::with_gil(|py| {
        let sys = py.import_bound("sys").unwrap();
        let modules = sys
            .getattr("modules")
            .unwrap()
            .downcast_into::<PyDict>()
            .unwrap();

        let crown_code = r#"
from typing import List, Tuple

def insight_semantic(text: str) -> List[Tuple[str, float]]:
    return [("joy", 0.75), (text, 0.5)]
"#;
        let crown = PyModule::from_code_bound(py, crown_code, "", "neoabzu_crown").unwrap();
        modules.set_item("neoabzu_crown", &crown).unwrap();

        let scores = crown_semantic(py, "hello crown").unwrap();
        assert_eq!(scores[0].0, "joy");
        assert!((scores[0].1 - 0.75).abs() < f32::EPSILON);
        assert_eq!(scores[1].0, "hello crown");
        assert!((scores[1].1 - 0.5).abs() < f32::EPSILON);
    });
}
