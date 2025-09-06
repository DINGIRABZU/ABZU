__version__ = "0.1.0"

import json
import sys
from pathlib import Path

from pytest import MonkeyPatch

import razar.boot_orchestrator as bo
import razar.ai_invoker as ai_invoker


class DummyProc:
    returncode = 0

    def terminate(self) -> None:  # pragma: no cover - trivial
        pass

    def wait(self) -> None:  # pragma: no cover - trivial
        pass


def test_long_task_retries_until_success(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Long task mode keeps invoking handover until a patch succeeds."""
    handover_calls = {"count": 0}

    def fake_handover(component: str, error: str, use_opencode: bool = False) -> bool:
        handover_calls["count"] += 1
        return handover_calls["count"] == 2

    monkeypatch.setattr(ai_invoker, "handover", fake_handover)

    launch_attempts = {"count": 0}

    def fake_launch(comp):
        launch_attempts["count"] += 1
        if launch_attempts["count"] == 1:
            raise RuntimeError("boom")
        return DummyProc()

    monkeypatch.setattr(bo, "launch_component", fake_launch)

    # Redirect file paths used by boot orchestrator
    monkeypatch.setattr(bo, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(bo, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", tmp_path / "invocations.json")
    monkeypatch.setattr(bo, "LONG_TASK_LOG_PATH", tmp_path / "long_task.json")
    monkeypatch.setattr(bo, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(bo, "_perform_handshake", lambda comps: None)
    monkeypatch.setattr(bo, "launch_required_agents", lambda: None)
    monkeypatch.setattr(bo.doc_sync, "sync_docs", lambda: None)
    monkeypatch.setattr(bo, "_log_ai_invocation", lambda *a, **k: None)
    monkeypatch.setattr(bo.time, "sleep", lambda *a, **k: None)

    config = {
        "components": [
            {"name": "demo", "command": ["echo", "hi"], "health_check": ["true"]}
        ]
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(config))

    argv = [
        "bo",
        "--config",
        str(cfg_path),
        "--retries",
        "0",
        "--long-task",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    bo.main()

    entries = json.loads((tmp_path / "long_task.json").read_text())
    assert len(entries) == 2
    assert entries[0]["patched"] is False
    assert entries[1]["patched"] is True
    assert handover_calls["count"] == 2
    history = json.loads((tmp_path / "history.json").read_text())
    comp = history["history"][0]["components"][0]
    assert comp["success"] is True
    assert comp["attempts"] == 2
