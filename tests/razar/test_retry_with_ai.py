"""Tests for retry logic with Opencode patch."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from pytest import MonkeyPatch

import razar.boot_orchestrator as bo


class DummyProc(SimpleNamespace):
    returncode = 0

    def terminate(self) -> None:  # pragma: no cover - trivial
        pass

    def wait(self) -> None:  # pragma: no cover - trivial
        pass


def test_retry_with_ai_applies_patch_and_relaunches(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Component restarts after Opencode patch and logs are updated."""
    patch_log = tmp_path / "patch_log.json"
    inv_log = tmp_path / "invocations.json"
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(bo.ai_invoker, "PATCH_LOG_PATH", patch_log)

    calls: dict[str, object] = {}

    def fake_handover(component: str, error: str, use_opencode: bool = False) -> bool:
        calls["handover"] = (component, error, use_opencode)
        bo.ai_invoker._append_patch_log(
            {
                "event": "patch_attempt",
                "component": component,
                "module": "dummy",
                "attempt": 1,
                "success": True,
                "timestamp": "now",
            }
        )
        return True

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)

    def fake_health(name: str) -> bool:
        calls["health"] = name
        return True

    monkeypatch.setattr(bo.health_checks, "run", fake_health)

    def fake_launch(comp):
        calls["launch"] = comp
        return DummyProc()

    monkeypatch.setattr(bo, "launch_component", fake_launch)

    component = {"name": "demo", "command": ["echo", "hi"]}
    proc, attempts, err = bo._retry_with_ai("demo", component, "boom", 1)

    assert proc is not None and attempts == 1
    assert calls["handover"] == ("demo", "boom", True)
    assert calls["health"] == "demo"
    assert calls["launch"] == component

    log = json.loads(patch_log.read_text())
    assert log and log[0]["component"] == "demo" and log[0]["success"] is True
