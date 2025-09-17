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
        self.last_prompt = ""
    def complete(self, prompt):
        self.calls += 1
        self.last_prompt = prompt
        return prompt
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
        let doctrine_path = docs_dir.join("The_Absolute_Protocol.md");
        std::fs::write(&doctrine_path, "protocol doctrine").unwrap();
        let blueprint_path = docs_dir.join("system_blueprint.md");
        std::fs::write(&blueprint_path, "blueprint doctrine").unwrap();
        let awakening_path = docs_dir.join("awakening_overview.md");
        std::fs::write(&awakening_path, "awakening doctrine").unwrap();

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
                "extra_paths",
                PyList::new(
                    py,
                    vec![
                        doctrine_path.to_str().unwrap(),
                        blueprint_path.to_str().unwrap(),
                        awakening_path.to_str().unwrap(),
                    ],
                ),
            )
            .unwrap();

        let res: String = func
            .call((integ,), Some(kwargs))
            .unwrap()
            .extract()
            .unwrap();
        assert!(res.contains("mission"));
        assert!(res.contains("persona"));
        assert!(res.contains("protocol doctrine"));
        assert!(res.contains("blueprint doctrine"));
        assert!(res.contains("awakening doctrine"));
        assert!(identity_path.exists());
        let res2: String = func
            .call((integ,), Some(kwargs))
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(res2, res);
        let calls: i32 = integ.getattr("calls").unwrap().extract().unwrap();
        assert_eq!(calls, 1);
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
        let called: bool = flag
            .get_item("called")
            .unwrap()
            .unwrap()
            .extract()
            .unwrap();
        assert!(called);
    });
}
