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
    monkeypatch.setattr(ai_invoker.health_checks, "run", lambda name: True)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", tmp_path / "patch.json")

    result = ai_invoker.handover("comp", "boom", use_opencode=True)
    assert result is True
    assert called["module"] == tmp_path / "mod.py"
    assert called["tests"] == [tmp_path / "test_mod.py"]
    assert called["error"] == "boom"


def test_handover_snapshots_target_before_patch(monkeypatch, tmp_path: Path) -> None:
    module_path = tmp_path / "mod.py"
    module_path.write_text("original", encoding="utf-8")

    diff = f"+++ b/{module_path}\n"

    monkeypatch.setattr(
        ai_invoker.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
    )
    monkeypatch.setattr(ai_invoker.opencode_client, "complete", lambda ctx: diff)

    backups = tmp_path / "backups"
    monkeypatch.setattr(ai_invoker, "PATCH_BACKUP_DIR", backups)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", tmp_path / "patch.json")

    monkeypatch.setattr(
        code_repair_module,
        "repair_module",
        lambda module, tests, err: True,
    )
    monkeypatch.setattr(ai_invoker.health_checks, "run", lambda name: True)

    result = ai_invoker.handover("comp", "boom", use_opencode=True)
    assert result is True
    snaps = list(backups.iterdir())
    assert len(snaps) == 1
    assert snaps[0].read_text(encoding="utf-8") == "original"


def test_handover_rolls_back_on_failed_check(monkeypatch, tmp_path: Path) -> None:
    module_path = tmp_path / "mod.py"
    module_path.write_text("original", encoding="utf-8")

    diff = f"+++ b/{module_path}\n"

    monkeypatch.setattr(
        ai_invoker.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
    )
    monkeypatch.setattr(ai_invoker.opencode_client, "complete", lambda ctx: diff)

    backups = tmp_path / "backups"
    monkeypatch.setattr(ai_invoker, "PATCH_BACKUP_DIR", backups)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", tmp_path / "patch.json")

    def fake_repair(module, tests, err):
        module.write_text("patched", encoding="utf-8")
        return True

    monkeypatch.setattr(code_repair_module, "repair_module", fake_repair)
    monkeypatch.setattr(ai_invoker.health_checks, "run", lambda name: False)

    result = ai_invoker.handover("comp", "boom", use_opencode=True)
    assert result is False
    assert module_path.read_text(encoding="utf-8") == "original"
    snaps = list(backups.iterdir())
    assert len(snaps) == 1
