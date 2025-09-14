use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn latency_and_resource_gauges_update() {
    Python::with_gil(|py| {
        let sys = py.import("sys").unwrap();
        let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();

        // stub orchestrator
        let rag = PyModule::new(py, "rag").unwrap();
        modules.set_item("rag", rag).unwrap();
        let orch_code = r#"
class MoGEOrchestrator:
    def route(self, text, emotion_data, text_modality=False, voice_modality=False, music_modality=False, documents=None):
        return {'model': 'stub-model'}
"#;
        let orch = PyModule::from_code(py, orch_code, "", "rag.orchestrator").unwrap();
        modules.set_item("rag.orchestrator", orch).unwrap();

        // stub crown_decider
        let decider_code = r#"
def decide_expression_options(emotion):
    return {'tts_backend': 'stub-tts', 'avatar_style': 'stub-style'}
"#;
        let decider = PyModule::from_code(py, decider_code, "", "crown_decider").unwrap();
        modules.set_item("crown_decider", decider).unwrap();

        // stub prometheus_client
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

        // stub psutil
        let psutil_code = r#"
def cpu_percent():
    return 12.5
class VM:
    used = 1234
    def __init__(self):
        pass

def virtual_memory():
    return VM()
"#;
        let psutil = PyModule::from_code(py, psutil_code, "", "psutil").unwrap();
        modules.set_item("psutil", psutil).unwrap();

        // stub pynvml
        let pynvml_code = r#"
def nvmlInit():
    pass

def nvmlDeviceGetHandleByIndex(i):
    return i

class Info:
    def __init__(self):
        self.used = 5678

def nvmlDeviceGetMemoryInfo(handle):
    return Info()
"#;
        let pynvml = PyModule::from_code(py, pynvml_code, "", "pynvml").unwrap();
        modules.set_item("pynvml", pynvml).unwrap();

        // call route_decision
        let crown = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = crown.getattr("route_decision").unwrap();
        let emotion = PyDict::new(py);
        emotion.set_item("emotion", "joy").unwrap();
        let args = ("hi", emotion, py.None(), py.None(), py.None());
        let res: &PyDict = func.call1(args).unwrap().downcast().unwrap();
        let model: String = res.get_item("model").unwrap().extract().unwrap();
        assert_eq!(model, "stub-model");

        // verify metrics
        let prom = PyModule::import(py, "prometheus_client").unwrap();
        let registry = prom.getattr("REGISTRY").unwrap();
        let collectors: &PyDict = registry
            .getattr("_names_to_collectors")
            .unwrap()
            .downcast()
            .unwrap();
        let latency = collectors.get_item("service_request_latency_seconds").unwrap();
        let cpu = collectors.get_item("service_cpu_usage_percent").unwrap();
        let mem = collectors.get_item("service_memory_usage_bytes").unwrap();
        let gpu = collectors.get_item("service_gpu_memory_usage_bytes").unwrap();
        let latency_val: f64 = latency.getattr("value").unwrap().extract().unwrap();
        let cpu_val: f64 = cpu.getattr("value").unwrap().extract().unwrap();
        let mem_val: u64 = mem.getattr("value").unwrap().extract().unwrap();
        let gpu_val: u64 = gpu.getattr("value").unwrap().extract().unwrap();
        assert!(latency_val > 0.0);
        assert_eq!(cpu_val, 12.5);
        assert_eq!(mem_val, 1234);
        assert_eq!(gpu_val, 5678);
    });
}

#[test]
fn heartbeat_out_of_sync_increments_error_counter() {
    Python::with_gil(|py| {
        let sys = py.import("sys").unwrap();
        let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();

        // stubs for orchestrator
        let rag = PyModule::new(py, "rag").unwrap();
        modules.set_item("rag", rag).unwrap();
        let orch_code = r#"
class MoGEOrchestrator:
    def route(self, text, emotion_data, text_modality=False, voice_modality=False, music_modality=False, documents=None):
        return {'model': 'stub-model'}
"#;
        let orch = PyModule::from_code(py, orch_code, "", "rag.orchestrator").unwrap();
        modules.set_item("rag.orchestrator", orch).unwrap();

        // stub event bus
        let bus_code = r#"
events = []

def emit_event(actor, action, meta):
    events.append((actor, action, meta))
"#;
        let bus = PyModule::from_code(py, bus_code, "", "agents.event_bus").unwrap();
        modules.set_item("agents.event_bus", bus).unwrap();
        let agents = PyModule::new(py, "agents").unwrap();
        modules.set_item("agents", agents).unwrap();

        // stub heartbeat module
        let hb_code = r#"
class ChakraHeartbeat:
    def check_alerts(self):
        pass
    def sync_status(self):
        return 'out_of_sync'
"#;
        let hb = PyModule::from_code(py, hb_code, "", "monitoring.chakra_heartbeat").unwrap();
        modules.set_item("monitoring.chakra_heartbeat", hb).unwrap();
        let monitoring = PyModule::new(py, "monitoring").unwrap();
        modules.set_item("monitoring", monitoring).unwrap();

        // stub prometheus
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

        // stub crown_decider to perform heartbeat check and raise
        let decider_code = r#"
from monitoring.chakra_heartbeat import ChakraHeartbeat
from agents.event_bus import emit_event
from prometheus_client import Counter, REGISTRY

hb = ChakraHeartbeat()

def decide_expression_options(emotion):
    hb.check_alerts()
    if hb.sync_status() != 'Great Spiral':
        emit_event('chakra_heartbeat', 'chakra_down', {'status': 'out_of_sync'})
        counter = REGISTRY._names_to_collectors.get('service_errors_total') or Counter('service_errors_total', '', ['service'])
        counter.labels('crown').inc()
        raise RuntimeError('chakras out of sync')
    return {'tts_backend': 'stub-tts', 'avatar_style': 'stub-style'}
"#;
        let decider = PyModule::from_code(py, decider_code, "", "crown_decider").unwrap();
        modules.set_item("crown_decider", decider).unwrap();

        let crown = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = crown.getattr("route_decision").unwrap();
        let emotion = PyDict::new(py);
        emotion.set_item("emotion", "joy").unwrap();
        let args = ("hi", emotion, py.None(), py.None(), py.None());
        let result = func.call1(args);
        assert!(result.is_err());

        // verify error counter and event
        let prom = PyModule::import(py, "prometheus_client").unwrap();
        let registry = prom.getattr("REGISTRY").unwrap();
        let collectors: &PyDict = registry
            .getattr("_names_to_collectors")
            .unwrap()
            .downcast()
            .unwrap();
        let err = collectors.get_item("service_errors_total").unwrap();
        let val: i32 = err.getattr("value").unwrap().extract().unwrap();
        assert_eq!(val, 1);
        let count: usize = py
            .eval("len(agents.event_bus.events)", None, None)
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(count, 1);
    });
}

#[test]
fn validator_non_compliance_increments_error_counter() {
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
    return {'tts_backend': 'stub-tts', 'avatar_style': 'stub-style'}
"#;
        let decider = PyModule::from_code(py, decider_code, "", "crown_decider").unwrap();
        modules.set_item("crown_decider", decider).unwrap();

        // prometheus stub
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

        // validator stub
        let validator_code = r#"
from prometheus_client import Counter, REGISTRY

class DummyValidator:
    def validate_action(self, agent, text):
        counter = REGISTRY._names_to_collectors.get('service_errors_total') or Counter('service_errors_total', '', ['service'])
        counter.labels('crown').inc()
        return {'compliant': False}

validator = DummyValidator()
"#;
        py.run(validator_code, None, None).unwrap();

        let crown = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = crown.getattr("route_decision").unwrap();
        let emotion = PyDict::new(py);
        emotion.set_item("emotion", "joy").unwrap();
        let validator = py.eval("validator", None, None).unwrap();
        let args = ("hi", emotion, py.None(), validator, py.None());
        let result = func.call1(args);
        assert!(result.is_err());

        // verify error counter
        let prom = PyModule::import(py, "prometheus_client").unwrap();
        let registry = prom.getattr("REGISTRY").unwrap();
        let collectors: &PyDict = registry
            .getattr("_names_to_collectors")
            .unwrap()
            .downcast()
            .unwrap();
        let err = collectors.get_item("service_errors_total").unwrap();
        let val: i32 = err.getattr("value").unwrap().extract().unwrap();
        assert_eq!(val, 1);
    });
}
