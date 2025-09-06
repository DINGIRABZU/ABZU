"""Tests remote repair through the boot orchestrator."""

__version__ = "0.1.0"

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence
import pytest
from pytest import MonkeyPatch

import razar.boot_orchestrator as bo
import razar.ai_invoker as ai_invoker
import agents.razar.code_repair as code_repair_module
from tools import opencode_client


@pytest.mark.parametrize("backend", ["", "kimi"])
def test_remote_repair(tmp_path: Path, monkeypatch: MonkeyPatch, backend: str) -> None:
    """Boot orchestrator applies AI patch and relaunches component."""
    # Configure opencode backend
    monkeypatch.setenv("OPENCODE_BACKEND", backend)
    monkeypatch.setattr(opencode_client, "_BACKEND", backend)

    calls = {"complete": 0, "repair": 0}

    def fake_complete(prompt: str) -> str:
        calls["complete"] += 1
        return "diff"

    monkeypatch.setattr(opencode_client, "complete", fake_complete)

    probe_state = {"patched": False}

    def fake_repair(module_path: Path, tests: Sequence[Path], err: str) -> bool:
        calls["repair"] += 1
        probe_state["patched"] = True
        return True

    monkeypatch.setattr(code_repair_module, "repair_module", fake_repair)

    def fake_cli(
        cmd: list[str],
        input: str | None = None,
        capture_output: Any = None,
        text: Any = None,
        check: Any = None,
    ) -> SimpleNamespace:
        assert cmd == ["opencode", "run", "--json"]
        opencode_client.complete("ctx")
        suggestion = [{"module": "dummy", "tests": [], "error": "boom"}]
        return SimpleNamespace(returncode=0, stdout=json.dumps(suggestion))

    monkeypatch.setattr(ai_invoker.subprocess, "run", fake_cli)
    monkeypatch.setattr(ai_invoker, "PATCH_LOG_PATH", tmp_path / "patch_log.json")

    # Redirect file paths used by boot orchestrator
    monkeypatch.setattr(bo, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(bo, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", tmp_path / "invocations.json")
    monkeypatch.setattr(bo, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(bo, "_perform_handshake", lambda comps: None)
    monkeypatch.setattr(bo, "launch_required_agents", lambda: None)
    monkeypatch.setattr(bo.doc_sync, "sync_docs", lambda: None)
    monkeypatch.setattr(bo, "_log_ai_invocation", lambda *a, **k: None)
    monkeypatch.setattr(bo.time, "sleep", lambda *a, **k: None)

    class DummyProc:
        returncode = 0

        def terminate(self) -> None:  # pragma: no cover - trivial
            pass

        def wait(self) -> None:  # pragma: no cover - trivial
            pass

    monkeypatch.setattr(bo.subprocess, "Popen", lambda *a, **k: DummyProc())

    def fake_probe(name: str) -> bool:
        return probe_state["patched"]

    monkeypatch.setattr(bo.health_checks, "run", fake_probe)
    monkeypatch.setitem(bo.health_checks.CHECKS, "demo", fake_probe)

    config = {"components": [{"name": "demo", "command": ["echo", "hi"]}]}
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(config))

    argv = ["bo", "--config", str(cfg_path), "--retries", "0", "--remote-attempts", "1"]
    monkeypatch.setattr(sys, "argv", argv)
    bo.main()

    assert calls["complete"] == 1
    assert calls["repair"] == 1
    assert probe_state["patched"] is True

    history = json.loads((tmp_path / "history.json").read_text())
    comp = history["history"][0]["components"][0]
    assert comp["success"] is True
    assert comp["attempts"] == 2
