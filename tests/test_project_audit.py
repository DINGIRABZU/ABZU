import sys

import tools.project_audit as audit


def test_check_module_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "PROJECT_ROOT", tmp_path)
    errors = audit.check_module("no_module")
    assert errors == ["no_module.py not found"]


def test_check_module_missing_dependency(tmp_path, monkeypatch):
    module = tmp_path / "temp_mod.py"
    module.write_text("import nonexistent_dep\n")
    monkeypatch.setattr(audit, "PROJECT_ROOT", tmp_path)
    sys.path.insert(0, str(tmp_path))
    try:
        errors = audit.check_module("temp_mod")
    finally:
        sys.path.remove(str(tmp_path))
    assert errors == ["Missing dependency 'nonexistent_dep' required by temp_mod"]

