use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn falls_back_to_kimicho_on_error() {
    Python::with_gil(|py| {
        let sys = py.import("sys").unwrap();
        let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();

        // crown stub that raises
        let crown_code = "def route_decision(text, emotion):\n raise Exception('fail')";
        let crown = PyModule::from_code(py, crown_code, "", "neoabzu_crown").unwrap();
        modules.set_item("neoabzu_crown", crown).unwrap();

        // kimicho stub
        let kimi_code = "def fallback_k2(prompt):\n return prompt.upper()";
        let kimi = PyModule::from_code(py, kimi_code, "", "neoabzu_kimicho").unwrap();
        modules.set_item("neoabzu_kimicho", kimi).unwrap();

        let binding = neoabzu_razar::route(py, "hi", "neutral").unwrap();
        let res: &PyDict = binding.as_ref(py).downcast().unwrap();
        let text: String = res.get_item("text").unwrap().unwrap().extract().unwrap();
        assert_eq!(text, "HI");
    });
}
