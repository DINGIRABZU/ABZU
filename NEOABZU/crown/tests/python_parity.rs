use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn rust_matches_python_route_decision() {
    Python::with_gil(|py| {
        py.run(
            r#"
import types, sys, asyncio, json

class DummyOrchestrator:
    def __init__(self):
        self.called = False
    def route(self, text, emotion_data, text_modality=False, voice_modality=False, music_modality=False, documents=None):
        self.called = True
        return {'model': 'test-model'}

class DummyValidator:
    def validate_action(self, agent, text):
        return {'compliant': True}

def decide_expression_options(emotion):
    return {'tts_backend': 'tts', 'avatar_style': 'avatar', 'aura': 'blue'}

def get_soul_state():
    return 'calm'

class DocumentRegistry:
    def get_corpus(self):
        return {'doc': 'value'}

class ChakraHeartbeat:
    def check_alerts(self):
        pass
    def sync_status(self):
        return 'Great Spiral'

def emit_event(actor, action, meta):
    pass

# stub modules
crown_decider = types.ModuleType('crown_decider')
crown_decider.decide_expression_options = decide_expression_options
sys.modules['crown_decider'] = crown_decider

emotional_state = types.ModuleType('emotional_state')
emotional_state.get_soul_state = get_soul_state
sys.modules['emotional_state'] = emotional_state

agents = types.ModuleType('agents')
event_bus = types.ModuleType('event_bus')
event_bus.emit_event = emit_event
agents.event_bus = event_bus
sys.modules['agents'] = agents
sys.modules['agents.event_bus'] = event_bus

rag = types.ModuleType('rag')
orchestrator = types.ModuleType('orchestrator')
orchestrator.MoGEOrchestrator = DummyOrchestrator
rag.orchestrator = orchestrator
sys.modules['rag'] = rag
sys.modules['rag.orchestrator'] = orchestrator

INANNA_AI = types.ModuleType('INANNA_AI')
ethical = types.ModuleType('ethical_validator')
ethical.EthicalValidator = DummyValidator
INANNA_AI.ethical_validator = ethical
sys.modules['INANNA_AI'] = INANNA_AI
sys.modules['INANNA_AI.ethical_validator'] = ethical

doc_mod = types.ModuleType('agents.nazarick.document_registry')
doc_mod.DocumentRegistry = DocumentRegistry
sys.modules['agents.nazarick.document_registry'] = doc_mod

monitoring = types.ModuleType('monitoring')
chakra_mod = types.ModuleType('chakra_heartbeat')
chakra_mod.ChakraHeartbeat = ChakraHeartbeat
monitoring.chakra_heartbeat = chakra_mod
sys.modules['monitoring'] = monitoring
sys.modules['monitoring.chakra_heartbeat'] = chakra_mod

prom = types.ModuleType('prometheus_client')
class Counter:
    def __init__(self,*a,**k):
        pass
    def labels(self,*a):
        return self
    def inc(self):
        pass
prom.Counter = Counter
prom.REGISTRY = types.SimpleNamespace()
sys.modules['prometheus_client'] = prom

psutil = types.ModuleType('psutil')
psutil.cpu_percent = lambda :0
psutil.virtual_memory = lambda : types.SimpleNamespace(used=0)
sys.modules['psutil'] = psutil

neoabzu_memory = types.ModuleType('neoabzu_memory')
neoabzu_memory.query_memory = lambda text: {}
neoabzu_memory.broadcast_layer_event = lambda s: None
sys.modules['neoabzu_memory'] = neoabzu_memory
"#,
            None,
            None,
        )
        .unwrap();

        let py_router = PyModule::import(py, "crown_router").unwrap();
        let rs_router = PyModule::import(py, "neoabzu_crown").unwrap();

        let emotion = PyDict::new(py);
        emotion.set_item("emotion", "joy").unwrap();

        let py_dec: &PyDict = py_router
            .getattr("route_decision")
            .unwrap()
            .call1(("hello", emotion))
            .unwrap()
            .downcast()
            .unwrap();
        let rs_dec: &PyDict = rs_router
            .getattr("route_decision")
            .unwrap()
            .call1(("hello", emotion))
            .unwrap()
            .downcast()
            .unwrap();

        let model_py: String = py_dec.get_item("model").unwrap().unwrap().extract().unwrap();
        let model_rs: String = rs_dec.get_item("model").unwrap().unwrap().extract().unwrap();
        assert_eq!(model_py, model_rs);
        let tts_py: String = py_dec
            .get_item("tts_backend")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        let tts_rs: String = rs_dec
            .get_item("tts_backend")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(tts_py, tts_rs);
        let avatar_py: String = py_dec
            .get_item("avatar_style")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        let avatar_rs: String = rs_dec
            .get_item("avatar_style")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(avatar_py, avatar_rs);
    });
}
