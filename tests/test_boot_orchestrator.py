from __future__ import annotations

import json
from types import SimpleNamespace

import razar.boot_orchestrator as bo


class DummyProc(SimpleNamespace):
    returncode = 0

    def terminate(self) -> None:  # pragma: no cover - trivial
        pass

    def wait(self) -> None:  # pragma: no cover - trivial
        pass


def test_rstar_escalation_after_ten_attempts(tmp_path, monkeypatch):
    """Escalates to rStar on the tenth remote attempt."""
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
        if len(attempts) == 10:
            bo._set_active_agent("rstar")
            suggestion["value"] = "use rstar"
            return True
        return False

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    proc, used_attempts, err = bo._retry_with_ai("demo", component, "boom", 10)

    assert proc is not None and used_attempts == 10
    assert attempts[:9] == ["demo_agent"] * 9
    assert attempts[9] == "rstar"
    log = json.loads(inv_log.read_text())
    assert any(
        e.get("event") == "escalation" and e.get("agent") == "rstar" for e in log
    )
    assert suggestion["value"] == "use rstar"
