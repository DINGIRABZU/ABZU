use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn legacy_and_rust_route_match() {
    Python::with_gil(|py| {
        let sys = py.import("sys").unwrap();
        let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();

        // orchestrator stub
        let rag = PyModule::new(py, "rag").unwrap();
        modules.set_item("rag", rag).unwrap();
        let orch_code = r#"
class MoGEOrchestrator:
    def route(self, text, emotion_data, text_modality=False, voice_modality=False, music_modality=False, documents=None):
        return {'model': 'basic-rag'}
"#;
        let orch = PyModule::from_code(py, orch_code, "", "rag.orchestrator").unwrap();
        modules.set_item("rag.orchestrator", orch).unwrap();

        // crown_decider stub matching Rust logic
        let decider_code = r#"
import math

def decide_expression_options(emotion):
    e = emotion.lower()
    backend = 'bark' if e in ('anger', 'fear') else 'gtts'
    if e == 'joy':
        avatar = 'Soprano'
    elif e == 'sadness':
        avatar = 'Baritone'
    else:
        avatar = 'Androgynous'
    return {'tts_backend': backend, 'avatar_style': avatar, 'aura': e}
"#;
        let decider = PyModule::from_code(py, decider_code, "", "crown_decider").unwrap();
        modules.set_item("crown_decider", decider).unwrap();

        py.run("import sys; sys.path.append('../..')", None, None).unwrap();
        let legacy = PyModule::import(py, "crown_router").unwrap();
        let legacy_func = legacy.getattr("route_decision").unwrap();

        let crown = PyModule::import(py, "neoabzu_crown").unwrap();
        let rust_func = crown.getattr("route_decision").unwrap();

        let emotion = PyDict::new(py);
        emotion.set_item("emotion", "joy").unwrap();
        let args_py = ("hi", emotion, py.None(), py.None(), py.None());
        let py_res: &PyDict = legacy_func.call1(args_py).unwrap().downcast().unwrap();
        let args_rs = ("hi", emotion, py.None(), py.None(), py.None());
        let rs_res: &PyDict = rust_func.call1(args_rs).unwrap().downcast().unwrap();

        let m1: String = py_res.get_item("model").unwrap().unwrap().extract().unwrap();
        let m2: String = rs_res.get_item("model").unwrap().unwrap().extract().unwrap();
        assert_eq!(m1, m2);
        let t1: String = py_res.get_item("tts_backend").unwrap().unwrap().extract().unwrap();
        let t2: String = rs_res.get_item("tts_backend").unwrap().unwrap().extract().unwrap();
        assert_eq!(t1, t2);
        let a1: String = py_res.get_item("avatar_style").unwrap().unwrap().extract().unwrap();
        let a2: String = rs_res.get_item("avatar_style").unwrap().unwrap().extract().unwrap();
        assert_eq!(a1, a2);
    });
}
