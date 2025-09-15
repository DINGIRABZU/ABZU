use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn razar_legacy_and_rust_match() {
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

        // legacy crown_router stub
        let legacy_code = r#"
import crown_decider
from rag import orchestrator

def route_decision(text, emotion_data, orchestrator=orchestrator.MoGEOrchestrator(), validator=None, documents=None):
    if validator:
        res = validator.validate_action('operator', text)
        if not res.get('compliant', True):
            raise ValueError('validation failed')
    routed = orchestrator.route(text, emotion_data, text_modality=False, voice_modality=False, music_modality=False, documents=documents)
    opts = crown_decider.decide_expression_options(emotion_data.get('emotion', 'neutral'))
    out = {'model': routed.get('model', 'basic-rag'), 'tts_backend': opts['tts_backend'], 'avatar_style': opts['avatar_style'], 'aura': opts['aura']}
    if 'documents' in routed:
        out['documents'] = routed['documents']
    return out
"#;
        let legacy = PyModule::from_code(py, legacy_code, "", "crown_router").unwrap();
        modules.set_item("crown_router", legacy).unwrap();

        // build razar agent with legacy and rust routes
        let razar_code = r#"
import crown_router
import neoabzu_crown as crown

def legacy_route():
    return crown_router.route_decision('hi', {'emotion':'joy'})

def rust_route():
    return crown.route_decision('hi', {'emotion':'joy'})
"#;
        let razar_mod = PyModule::from_code(py, razar_code, "", "razar_agent").unwrap();
        modules.set_item("razar_agent", razar_mod).unwrap();

        let legacy_res: &PyDict = razar_mod
            .getattr("legacy_route")
            .unwrap()
            .call0()
            .unwrap()
            .downcast()
            .unwrap();
        let rust_res: &PyDict = razar_mod
            .getattr("rust_route")
            .unwrap()
            .call0()
            .unwrap()
            .downcast()
            .unwrap();

        assert_eq!(legacy_res.get_item("model"), rust_res.get_item("model"));
        assert_eq!(
            legacy_res.get_item("tts_backend"),
            rust_res.get_item("tts_backend")
        );
        assert_eq!(
            legacy_res.get_item("avatar_style"),
            rust_res.get_item("avatar_style")
        );
    });
}
