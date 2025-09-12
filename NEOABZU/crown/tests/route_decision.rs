use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn test_route_decision_invokes_orchestrator() {
    Python::with_gil(|py| {
        py.run(
            r#"
class DummyOrchestrator:
    def __init__(self):
        self.called = False
    def route(self, text, emotion_data, text_modality=False, voice_modality=False, music_modality=False, documents=None):
        self.called = True
        assert documents == {'doc': 'value'}
        return {'model': 'test-model'}

class DummyValidator:
    def validate_action(self, agent, text):
        return {'compliant': True}

def decide_expression_options(emotion):
    return {'tts_backend': 'test-tts', 'avatar_style': 'test-avatar'}

orchestrator = DummyOrchestrator()
validator = DummyValidator()
"#,
            None,
            None,
        )
        .unwrap();

        let module = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = module.getattr("route_decision").unwrap();
        let emotion = PyDict::new(py);
        emotion.set_item("emotion", "joy").unwrap();
        let docs = PyDict::new(py);
        docs.set_item("doc", "value").unwrap();
        let args = (
            "hi",
            emotion,
            py.eval("orchestrator", None, None).unwrap(),
            py.eval("validator", None, None).unwrap(),
        );
        let kwargs = PyDict::new(py);
        kwargs.set_item("documents", docs).unwrap();
        let res: &PyDict = func.call(args, Some(kwargs)).unwrap().downcast().unwrap();
        let model: String = res
            .get_item("model")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(model, "test-model");
        let called: bool = py
            .eval("orchestrator.called", None, None)
            .unwrap()
            .extract()
            .unwrap();
        assert!(called);
    });
}
