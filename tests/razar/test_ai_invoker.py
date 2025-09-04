"""Tests for razar.ai_invoker opencode integration."""

__version__ = "0.1.2"

import json
from types import SimpleNamespace
from pathlib import Path

import agents.razar.code_repair as code_repair_module
import razar.ai_invoker as ai_invoker


def test_handover_uses_opencode_and_applies_patch(monkeypatch, tmp_path: Path) -> None:
    suggestion = [
        {
            "module": str(tmp_path / "mod.py"),
            "tests": [str(tmp_path / "test_mod.py")],
            "error": "boom",
        }
    ]

    def fake_run(cmd, input=None, capture_output=None, text=None, check=None):
        assert cmd == ["opencode", "run", "--json"]
        assert json.loads(input) == {"component": "comp", "error": "boom"}
        return SimpleNamespace(returncode=0, stdout=json.dumps(suggestion))

    called: dict[str, object] = {}

    def fake_repair(module_path: Path, tests, err):
        called["module"] = module_path
        called["tests"] = list(tests)
        called["error"] = err
        return True

    monkeypatch.setattr(ai_invoker.subprocess, "run", fake_run)
    monkeypatch.setattr(code_repair_module, "repair_module", fake_repair)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", tmp_path / "patch.json")

    result = ai_invoker.handover("comp", "boom", use_opencode=True)
    assert result is True
    assert called["module"] == tmp_path / "mod.py"
    assert called["tests"] == [tmp_path / "test_mod.py"]
    assert called["error"] == "boom"
