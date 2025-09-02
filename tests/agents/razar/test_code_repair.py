"""Tests for code repair."""

__version__ = "0.2.2"

import json
from pathlib import Path

import agents.razar.code_repair as code_repair


def test_repair_module_applies_patch_and_logs(monkeypatch, tmp_path: Path) -> None:
    module = tmp_path / "mod.py"
    module.write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )

    test_file = tmp_path / "test_mod.py"
    test_file.write_text(
        "from mod import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    class DummyModel:
        def complete(self, context: str) -> str:
            return "def add(a, b):\n    return a + b\n"

    patch_log = tmp_path / "patches.json"
    monkeypatch.setattr(code_repair, "PATCH_LOG_PATH", patch_log)
    monkeypatch.setattr(code_repair, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        code_repair.quarantine_manager, "reactivate_component", lambda *a, **k: None
    )
    monkeypatch.setattr(code_repair.doc_sync, "sync_docs", lambda: None)
    monkeypatch.setattr(code_repair, "_run_tests", lambda paths, env: True)

    result = code_repair.repair_module(
        module, [test_file], "boom", models=[DummyModel()]
    )
    assert result is True
    assert module.read_text(encoding="utf-8").strip().endswith("return a + b")

    records = json.loads(patch_log.read_text(encoding="utf-8"))
    assert records[0]["event"] == "applied"
    assert records[0]["component"] == "mod"
