use pyo3::prelude::*;
use pyo3::types::PyDict;

fn setup_stub_layers(py: Python<'_>) {
    let sys = py.import("sys").unwrap();
    let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();

    macro_rules! stub {
        ($name:expr, $code:expr) => {
            let module = PyModule::from_code(py, $code, "", $name).unwrap();
            modules.set_item($name, module).unwrap();
        };
    }

    let agents = PyModule::new(py, "agents").unwrap();
    modules.set_item("agents", agents).unwrap();
    stub!(
        "agents.event_bus",
        "events = []\n\ndef emit_event(actor, action, metadata):\n    events.append((actor, action, metadata))\n"
    );

    stub!(
        "memory.cortex",
        "def query_spirals(**kw):\n    return ['c']\n"
    );
    stub!(
        "vector_memory",
        "def query_vectors(*a, **k):\n    return ['v']\n"
    );
    stub!(
        "spiral_memory",
        "def spiral_recall(q):\n    return 's'\n"
    );
    stub!(
        "memory.emotional",
        "def fetch_emotion_history(limit):\n    return ['e']\n"
    );
    stub!(
        "memory.mental",
        "def query_related_tasks(q):\n    return ['m']\n"
    );
    stub!(
        "memory.spiritual",
        "def lookup_symbol_history(q):\n    return ['p']\n"
    );
    stub!(
        "memory.narrative_engine",
        "def stream_stories():\n    return ['n']\n"
    );
    stub!(
        "neoabzu_core",
        "def evaluate(expr):\n    return 'core'\n"
    );
}

#[test]
fn crown_exposes_memory_query() {
    Python::with_gil(|py| {
        setup_stub_layers(py);
        let crown = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = crown.getattr("query_memory").unwrap();
        let res: Py<PyDict> = func.call1(("demo",)).unwrap().extract().unwrap();
        let d = res.as_ref(py);
        let cortex: Vec<String> = d.get_item("cortex").unwrap().unwrap().extract().unwrap();
        let vector: Vec<String> = d.get_item("vector").unwrap().unwrap().extract().unwrap();
        let spiral: String = d.get_item("spiral").unwrap().unwrap().extract().unwrap();
        let emotional: Vec<String> = d.get_item("emotional").unwrap().unwrap().extract().unwrap();
        let mental: Vec<String> = d.get_item("mental").unwrap().unwrap().extract().unwrap();
        let spiritual: Vec<String> = d.get_item("spiritual").unwrap().unwrap().extract().unwrap();
        let narrative: Vec<String> = d.get_item("narrative").unwrap().unwrap().extract().unwrap();
        let core: String = d.get_item("core").unwrap().unwrap().extract().unwrap();
        let failed: Vec<String> = d.get_item("failed_layers").unwrap().unwrap().extract().unwrap();
        assert_eq!(cortex, vec!["c"]);
        assert_eq!(vector, vec!["v"]);
        assert_eq!(spiral, "s");
        assert_eq!(emotional, vec!["e"]);
        assert_eq!(mental, vec!["m"]);
        assert_eq!(spiritual, vec!["p"]);
        assert_eq!(narrative, vec!["n"]);
        assert_eq!(core, "core");
        assert!(failed.is_empty());
    });
}

#[test]
fn crown_import_triggers_layer_init() {
    Python::with_gil(|py| {
        setup_stub_layers(py);
        PyModule::import(py, "neoabzu_crown").unwrap();
        let actor: String = py
            .eval("agents.event_bus.events[0][0]", None, None)
            .unwrap()
            .extract()
            .unwrap();
        let action: String = py
            .eval("agents.event_bus.events[0][1]", None, None)
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(actor, "memory");
        assert_eq!(action, "layer_init");
        for layer in [
            "cortex",
            "vector",
            "spiral",
            "emotional",
            "mental",
            "spiritual",
            "narrative",
            "core",
        ] {
            let check: bool = py
                .eval(&format!("'{layer}' in agents.event_bus.events[0][2]['layers']"), None, None)
                .unwrap()
                .extract()
                .unwrap();
            assert!(check);
        }
    });
}
