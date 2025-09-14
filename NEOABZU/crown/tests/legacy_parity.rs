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
        return {'model': 'stub-model'}
"#;
        let orch = PyModule::from_code(py, orch_code, "", "rag.orchestrator").unwrap();
        modules.set_item("rag.orchestrator", orch).unwrap();

        // crown_decider stub
        let decider_code = r#"
def decide_expression_options(emotion):
    return {'tts_backend': 'stub-tts', 'avatar_style': 'stub-style', 'aura': 'calm'}
"#;
        let decider = PyModule::from_code(py, decider_code, "", "crown_decider").unwrap();
        modules.set_item("crown_decider", decider).unwrap();

        // heartbeat and event bus stubs
        let bus_code = r#"
_events = []

def emit_event(actor, action, meta):
    _events.append((actor, action, meta))
"#;
        let bus = PyModule::from_code(py, bus_code, "", "agents.event_bus").unwrap();
        modules.set_item("agents.event_bus", bus).unwrap();
        let agents = PyModule::new(py, "agents").unwrap();
        modules.set_item("agents", agents).unwrap();

        let hb_code = r#"
class ChakraHeartbeat:
    def check_alerts(self):
        pass
    def sync_status(self):
        return 'Great Spiral'
"#;
        let hb = PyModule::from_code(py, hb_code, "", "monitoring.chakra_heartbeat").unwrap();
        modules.set_item("monitoring.chakra_heartbeat", hb).unwrap();
        let monitoring = PyModule::new(py, "monitoring").unwrap();
        modules.set_item("monitoring", monitoring).unwrap();

        // prometheus, psutil, pynvml stubs for telemetry
        let prom_code = r#"
class Metric:
    def __init__(self, name, desc, labels):
        self.value = 0
        REGISTRY._names_to_collectors[name] = self
    def labels(self, *a):
        return self
    def observe(self, v):
        self.value = v
    def set(self, v):
        self.value = v
    def inc(self, v=1):
        self.value += v
class Reg:
    def __init__(self):
        self._names_to_collectors = {}
REGISTRY = Reg()
Gauge = Histogram = Counter = Metric
"#;
        let prom = PyModule::from_code(py, prom_code, "", "prometheus_client").unwrap();
        modules.set_item("prometheus_client", prom).unwrap();

        let psutil_code = r#"
def cpu_percent():
    return 0.0
class VM:
    used = 0
    def __init__(self):
        pass

def virtual_memory():
    return VM()
"#;
        let psutil = PyModule::from_code(py, psutil_code, "", "psutil").unwrap();
        modules.set_item("psutil", psutil).unwrap();

        let pynvml_code = r#"
def nvmlInit():
    pass

def nvmlDeviceGetHandleByIndex(i):
    return i

class Info:
    def __init__(self):
        self.used = 0

def nvmlDeviceGetMemoryInfo(handle):
    return Info()
"#;
        let pynvml = PyModule::from_code(py, pynvml_code, "", "pynvml").unwrap();
        modules.set_item("pynvml", pynvml).unwrap();

        // ensure crown_router import path
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
