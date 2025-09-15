from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

import pytest
import razar.boot_orchestrator as bo
from tests.conftest import allow_test

allow_test(__file__)


class DummyProc(SimpleNamespace):
    returncode = 0

    def terminate(self) -> None:  # pragma: no cover - trivial
        pass

    def wait(self) -> None:  # pragma: no cover - trivial
        pass


@pytest.mark.parametrize("env_value, threshold", [(None, 9), ("11", 11)])
def test_rstar_escalation_after_threshold(tmp_path, monkeypatch, env_value, threshold):
    """Escalates to rStar once the configured threshold is reached."""
    if env_value is None:
        monkeypatch.delenv("RAZAR_RSTAR_THRESHOLD", raising=False)
    else:
        monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", env_value)
    importlib.reload(bo)

    inv_log = tmp_path / "invocations.json"
    cfg_path = tmp_path / "agents.json"
    cfg_path.write_text(
        json.dumps(
            {
                "active": "demo_agent",
                "agents": [{"name": "demo_agent"}, {"name": "rstar"}],
            }
        )
    )
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", cfg_path)

    attempts: list[str] = []
    suggestion: dict[str, str] = {}

    def fake_handover(component: str, error: str, use_opencode: bool = False):
        current = json.loads(cfg_path.read_text())["active"]
        attempts.append(current)
        if current == "rstar":
            suggestion["value"] = "use rstar"
            return True
        return False

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, used_attempts, err = bo._retry_with_ai(
        "demo", component, "boom", threshold + 1, failure_tracker
    )

    assert proc is not None and used_attempts == threshold + 1
    assert attempts[:threshold] == ["demo_agent"] * threshold
    assert attempts[threshold] == "rstar"
    log = json.loads(inv_log.read_text())
    assert any(
        e.get("event") == "escalation" and e.get("agent") == "rstar" for e in log
    )
    assert suggestion["value"] == "use rstar"
