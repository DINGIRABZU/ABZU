use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn razor_can_call_rust_router() {
    Python::with_gil(|py| {
        let sys = py.import("sys").unwrap();
        let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();

        // orchestrator stub for legacy crown_router
        let rag = PyModule::new(py, "rag").unwrap();
        modules.set_item("rag", rag).unwrap();
        let orch_code = r#"
class MoGEOrchestrator:
    def route(self, text, emotion_data, text_modality=False, voice_modality=False, music_modality=False, documents=None):
        return {'model': 'basic-rag'}
"#;
        let orch = PyModule::from_code(py, orch_code, "", "rag.orchestrator").unwrap();
        modules.set_item("rag.orchestrator", orch).unwrap();

        // decider stub matching Rust logic
        let decider_code = r#"
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
        let razor_code = r#"
import crown_router
import crown_router_rs

def legacy(text, emotion):
    return crown_router.route_decision(text, {'emotion': emotion})

def rust(text, emotion):
    return crown_router_rs.route_decision(text, {'emotion': emotion})
"#;
        let razor_mod = PyModule::from_code(py, razor_code, "", "razor_agent").unwrap();
        modules.set_item("razor_agent", razor_mod).unwrap();

        let legacy_res: &PyDict = py
            .eval("razor_agent.legacy('hi', 'joy')", None, None)
            .unwrap()
            .downcast()
            .unwrap();
        let rust_res: &PyDict = py
            .eval("razor_agent.rust('hi', 'joy')", None, None)
            .unwrap()
            .downcast()
            .unwrap();

        let m1: String = legacy_res.get_item("model").unwrap().unwrap().extract().unwrap();
        let m2: String = rust_res.get_item("model").unwrap().unwrap().extract().unwrap();
        assert_eq!(m1, m2);
        let t1: String = legacy_res.get_item("tts_backend").unwrap().unwrap().extract().unwrap();
        let t2: String = rust_res.get_item("tts_backend").unwrap().unwrap().extract().unwrap();
        assert_eq!(t1, t2);
    });
}
