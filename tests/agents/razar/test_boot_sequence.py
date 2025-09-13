"""Tests for boot sequence."""

import json
from pathlib import Path

import pytest

from razar import boot_orchestrator as bo


def test_boot_sequence_order_and_failure(tmp_path: Path, monkeypatch) -> None:
    config = {
        "components": [
            {"name": "alpha", "command": ["alpha"]},
            {"name": "beta", "command": ["beta"]},
            {"name": "gamma", "command": ["gamma"]},
        ]
    }
    cfg = tmp_path / "boot.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")

    events: list[str] = []

    def fake_run(name: str) -> bool:
        events.append(f"health:{name}")
        return name != "beta"

    monkeypatch.setattr(bo.health_checks, "run", fake_run)
    # Ensure load_config accepts components without explicit health checks
    monkeypatch.setitem(bo.health_checks.CHECKS, "alpha", lambda: True)
    monkeypatch.setitem(bo.health_checks.CHECKS, "beta", lambda: True)
    monkeypatch.setitem(bo.health_checks.CHECKS, "gamma", lambda: True)

    class DummyProc:
        def __init__(self, name: str) -> None:
            self.name = name
            events.append(f"launch:{name}")

        def wait(self) -> None:
            events.append(f"wait:{self.name}")

        def terminate(self) -> None:
            events.append(f"terminate:{self.name}")

    def fake_popen(cmd: list[str]):
        return DummyProc(cmd[0])

    monkeypatch.setattr(bo.subprocess, "Popen", fake_popen)

    components = bo.load_config(cfg)
    with pytest.raises(RuntimeError):
        for comp in components:
            bo.launch_component(comp)

    assert events == [
        "launch:alpha",
        "health:alpha",
        "launch:beta",
        "health:beta",
        "terminate:beta",
        "wait:beta",
    ]
    assert all(not e.startswith("launch:gamma") for e in events)
