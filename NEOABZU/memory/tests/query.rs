use neoabzu_memory::MemoryBundle;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

fn setup_stub_layers(py: Python<'_>) {
    let sys = py.import("sys").unwrap();
    let modules: &PyDict = sys.getattr("modules").unwrap().downcast().unwrap();

    macro_rules! stub {
        ($name:expr, $code:expr) => {
            let module = PyModule::from_code(py, $code, "", $name).unwrap();
            modules.set_item($name, module).unwrap();
        };
    }

    // memory and agents package placeholders
    let agents = PyModule::new(py, "agents").unwrap();
    modules.set_item("agents", agents).unwrap();
    let memory_pkg = PyModule::new(py, "memory").unwrap();
    modules.set_item("memory", memory_pkg).unwrap();
    let optional_pkg = PyModule::new(py, "memory.optional").unwrap();
    modules.set_item("memory.optional", optional_pkg).unwrap();
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
    stub!("spiral_memory", "def spiral_recall(q):\n    return 's'\n");
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
    stub!("neoabzu_core", "def evaluate(expr):\n    return expr\n");
}

#[test]
fn query_returns_all_layers() {
    Python::with_gil(|py| {
        setup_stub_layers(py);
        let mut bundle = MemoryBundle::new();
        bundle.initialize(py).unwrap();
        let res = bundle.query(py, "demo").unwrap();
        let d: &PyAny = res.as_ref(py);
        let cortex = d
            .get_item("cortex")
            .unwrap()
            .extract::<Vec<String>>()
            .unwrap();
        let vector = d
            .get_item("vector")
            .unwrap()
            .extract::<Vec<String>>()
            .unwrap();
        let spiral = d.get_item("spiral").unwrap().extract::<String>().unwrap();
        let emotional = d
            .get_item("emotional")
            .unwrap()
            .extract::<Vec<String>>()
            .unwrap();
        let mental = d
            .get_item("mental")
            .unwrap()
            .extract::<Vec<String>>()
            .unwrap();
        let spiritual = d
            .get_item("spiritual")
            .unwrap()
            .extract::<Vec<String>>()
            .unwrap();
        let narrative = d
            .get_item("narrative")
            .unwrap()
            .extract::<Vec<String>>()
            .unwrap();
        let failed = d
            .get_item("failed_layers")
            .unwrap()
            .extract::<Vec<String>>()
            .unwrap();
        assert_eq!(cortex, vec!["c"]);
        assert_eq!(vector, vec!["v"]);
        assert_eq!(spiral, "s");
        assert_eq!(emotional, vec!["e"]);
        assert_eq!(mental, vec!["m"]);
        assert_eq!(spiritual, vec!["p"]);
        assert_eq!(narrative, vec!["n"]);
        assert!(failed.is_empty());
    });
}

#[test]
fn query_handles_failed_layers() {
    Python::with_gil(|py| {
        let cases = [
            ("memory.cortex", "query_spirals", "cortex"),
            ("vector_memory", "query_vectors", "vector"),
            ("spiral_memory", "spiral_recall", "spiral"),
            ("memory.emotional", "fetch_emotion_history", "emotional"),
            ("memory.mental", "query_related_tasks", "mental"),
            ("memory.spiritual", "lookup_symbol_history", "spiritual"),
            ("memory.narrative_engine", "stream_stories", "narrative"),
        ];

        for (module_name, func_name, layer) in cases {
            setup_stub_layers(py);
            let sys = py.import("sys").unwrap();
            let modules: &PyDict = sys
                .getattr("modules")
                .unwrap()
                .downcast::<PyDict>()
                .unwrap();
            let module: &PyModule = modules
                .get_item(module_name)
                .unwrap()
                .unwrap()
                .downcast::<PyModule>()
                .unwrap();
            let boom = PyModule::from_code(
                py,
                "def f(*a, **k):\n    raise Exception('boom')\n",
                "",
                "boom",
            )
            .unwrap();
            module
                .setattr(func_name, boom.getattr("f").unwrap())
                .unwrap();

            let mut bundle = MemoryBundle::new();
            bundle.initialize(py).unwrap();
            let res = bundle.query(py, "demo").unwrap();
            let d: &PyAny = res.as_ref(py);
            let failed = d
                .get_item("failed_layers")
                .unwrap()
                .extract::<Vec<String>>()
                .unwrap();
            assert!(failed.contains(&layer.to_string()));
        }
    });
}
