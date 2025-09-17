use std::path::PathBuf;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyModule};
use tempfile::tempdir;

#[test]
fn load_identity_persists() {
    Python::with_gil(|py| {
        let module = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = module.getattr("load_identity").unwrap();
        let integration_code = r#"
class Dummy:
    def __init__(self):
        self.calls = 0
        self.prompts = []
    def complete(self, prompt):
        self.calls += 1
        self.prompts.append(prompt)
        if "CROWN-IDENTITY-ACK" in prompt:
            return "CROWN-IDENTITY-ACK"
        return "identity summary"
"#;
        let integ_mod = PyModule::from_code(py, integration_code, "", "").unwrap();
        let integ = integ_mod.getattr("Dummy").unwrap().call0().unwrap();

        let dir = tempdir().unwrap();
        let docs_dir = dir.path().join("docs");
        std::fs::create_dir_all(&docs_dir).unwrap();
        let mission_path = docs_dir.join("project_mission_vision.md");
        std::fs::write(&mission_path, "mission").unwrap();
        let persona_path = docs_dir.join("persona_api_guide.md");
        std::fs::write(&persona_path, "persona").unwrap();
        let genesis_dir = dir.path().join("GENESIS");
        let codex_dir = dir.path().join("CODEX").join("ACTIVATIONS");
        let inanna_dir = dir.path().join("INANNA_AI");
        std::fs::create_dir_all(&genesis_dir).unwrap();
        std::fs::create_dir_all(&codex_dir).unwrap();
        std::fs::create_dir_all(&inanna_dir).unwrap();
        let doctrine_docs = [
            (genesis_dir.join("GENESIS_.md"), "genesis"),
            (genesis_dir.join("SPIRAL_LAWS_.md"), "spiral"),
            (codex_dir.join("OATH_OF_THE_VAULT_.md"), "vault oath"),
            (
                inanna_dir.join("MARROW CODE 20545dfc251d80128395ffb5bc7725ee.md"),
                "marrow",
            ),
            (
                inanna_dir.join("INANNA SONG 20545dfc251d8065a32cec673272f292.md"),
                "song",
            ),
            (
                inanna_dir.join("Chapter I 1b445dfc251d802e860af64f2bf28729.md"),
                "chapter",
            ),
        ];
        for (path, text) in &doctrine_docs {
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent).unwrap();
            }
            std::fs::write(path, *text).unwrap();
        }
        let identity_path = dir.path().join("identity.json");

        let kwargs = PyDict::new(py);
        kwargs
            .set_item("mission_path", mission_path.to_str().unwrap())
            .unwrap();
        kwargs
            .set_item("persona_path", persona_path.to_str().unwrap())
            .unwrap();
        kwargs
            .set_item("identity_path", identity_path.to_str().unwrap())
            .unwrap();
        let doctrine_paths: Vec<String> = doctrine_docs
            .iter()
            .map(|(p, _)| p.to_str().unwrap().to_string())
            .collect();
        kwargs
            .set_item("doctrine_paths", PyList::new(py, &doctrine_paths))
            .unwrap();

        let res: String = func
            .call((integ.clone(),), Some(kwargs))
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(res, "identity summary");
        assert!(identity_path.exists());
        let res2: String = func
            .call((integ.clone(),), Some(kwargs))
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(res2, "identity summary");
        let calls: i32 = integ.getattr("calls").unwrap().extract().unwrap();
        assert_eq!(calls, 2);
        let prompts: Vec<String> = integ.getattr("prompts").unwrap().extract().unwrap();
        assert_eq!(prompts.len(), 2);
        let blended = &prompts[0];
        assert!(blended.contains("mission"));
        assert!(blended.contains("persona"));
        for (path, text) in &doctrine_docs {
            assert!(blended.contains(text));
            assert!(blended.contains(path.to_str().unwrap()));
        }
        assert!(prompts[1].contains("CROWN-IDENTITY-ACK"));
    });
}

#[test]
fn initialize_triggers_identity() {
    Python::with_gil(|py| {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..");
        let cmd = format!("import sys; sys.path.append('{}')", root.display());
        py.run(cmd.as_str(), None, None).unwrap();

        let init = PyModule::import(py, "init_crown_agent").unwrap();
        let dummy_code = r#"
class DummyGLM:
    def complete(self, prompt):
        return ''
    def health_check(self):
        pass
"#;
        let dummy_mod = PyModule::from_code(py, dummy_code, "", "").unwrap();
        let dummy_cls = dummy_mod.getattr("DummyGLM").unwrap();
        init.setattr("GLMIntegration", dummy_cls).unwrap();
        init.setattr(
            "_init_memory",
            py.eval("lambda cfg: None", None, None).unwrap(),
        )
        .unwrap();
        init.setattr(
            "_init_servants",
            py.eval("lambda cfg: None", None, None).unwrap(),
        )
        .unwrap();
        init.setattr(
            "_verify_servant_health",
            py.eval("lambda servants: None", None, None).unwrap(),
        )
        .unwrap();
        init.setattr(
            "_check_glm",
            py.eval("lambda integration: None", None, None).unwrap(),
        )
        .unwrap();

        let flag = PyDict::new(py);
        flag.set_item("called", false).unwrap();
        let globals = PyDict::new(py);
        globals.set_item("flag", flag).unwrap();
        let load_func = py
            .eval(
                "lambda integration: flag.__setitem__('called', True)",
                Some(globals),
                None,
            )
            .unwrap();
        init.setattr("load_identity", load_func).unwrap();

        init.getattr("initialize_crown").unwrap().call0().unwrap();
        let called: bool = flag.get_item("called").unwrap().extract().unwrap();
        assert!(called);
    });
}

#[test]
fn load_identity_requires_ack() {
    Python::with_gil(|py| {
        let module = PyModule::import(py, "neoabzu_crown").unwrap();
        let func = module.getattr("load_identity").unwrap();
        let integration_code = r#"
class NoAck:
    def __init__(self):
        self.prompts = []
    def complete(self, prompt):
        self.prompts.append(prompt)
        if "CROWN-IDENTITY-ACK" in prompt:
            return "nope"
        return "identity summary"
"#;
        let integ_mod = PyModule::from_code(py, integration_code, "", "").unwrap();
        let integ = integ_mod.getattr("NoAck").unwrap().call0().unwrap();

        let dir = tempdir().unwrap();
        let mission_path = dir.path().join("mission.md");
        std::fs::write(&mission_path, "mission").unwrap();
        let persona_path = dir.path().join("persona.md");
        std::fs::write(&persona_path, "persona").unwrap();
        let doctrine_path = dir.path().join("GENESIS").join("GENESIS_.md");
        if let Some(parent) = doctrine_path.parent() {
            std::fs::create_dir_all(parent).unwrap();
        }
        std::fs::write(&doctrine_path, "genesis").unwrap();
        let identity_path = dir.path().join("identity.json");

        let kwargs = PyDict::new(py);
        kwargs
            .set_item("mission_path", mission_path.to_str().unwrap())
            .unwrap();
        kwargs
            .set_item("persona_path", persona_path.to_str().unwrap())
            .unwrap();
        kwargs
            .set_item("identity_path", identity_path.to_str().unwrap())
            .unwrap();
        kwargs
            .set_item(
                "doctrine_paths",
                PyList::new(py, &[doctrine_path.to_str().unwrap()]),
            )
            .unwrap();

        let err = func.call((integ.clone(),), Some(kwargs)).unwrap_err();
        assert!(identity_path.exists() == false);
        let msg = err.to_string();
        assert!(msg.contains("CROWN-IDENTITY-ACK"));
    });
}
