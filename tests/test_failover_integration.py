import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import razar.bootstrap_utils as bootstrap_utils
import razar.boot_orchestrator as bo
import razar.utils.logging as razar_logging
from tests.conftest import allow_test

allow_test(__file__)


class DummyProc(SimpleNamespace):
    """Minimal process stub used by retry logic."""

    returncode = 0

    def terminate(self) -> None:  # pragma: no cover - trivial
        pass

    def wait(self) -> None:  # pragma: no cover - trivial
        pass


def configure_invocation_log(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    """Point the invocation log helper at ``path`` for the duration of the test."""

    monkeypatch.setattr(razar_logging, "INVOCATION_LOG_PATH", path)
    monkeypatch.setattr(razar_logging, "_LEGACY_CONVERTED", False)


def simulate_handshake_failure(
    monkeypatch: pytest.MonkeyPatch, component: str, logs_dir: Path
) -> list[str]:
    """Trigger the Crown handshake fallback and record the invoked endpoints."""

    fallback_targets: list[str] = []

    async def failing_handshake(_: str):
        raise RuntimeError("crown offline")

    def fake_init_kimicho(endpoint: str) -> None:
        fallback_targets.append(endpoint)

    monkeypatch.setattr(bo.crown_handshake, "perform", failing_handshake)
    monkeypatch.setattr(bo, "init_kimicho", fake_init_kimicho)
    monkeypatch.setattr(bo, "_persist_handshake", lambda response: None)
    monkeypatch.setattr(bo, "_ensure_glm4v", lambda capabilities: None)
    monkeypatch.setattr(bo, "_emit_event", lambda *a, **k: None)
    monkeypatch.setattr(bo.mission_logger, "log_event", lambda *a, **k: None)
    monkeypatch.setattr(bo, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(bootstrap_utils, "LOGS_DIR", logs_dir)

    with pytest.raises(RuntimeError, match="CROWN handshake failed"):
        bo._perform_handshake([{"name": component}])

    razar_logging.append_invocation_event(
        {
            "component": component,
            "event": "handshake",
            "agent": "crown",
            "agent_original": "Crown",
            "error": "crown offline",
            "attempt": 0,
            "patched": False,
        }
    )
    razar_logging.append_invocation_event(
        {
            "component": component,
            "event": "fallback",
            "agent": "kimicho",
            "agent_original": "Kimi-cho",
            "error": "kimicho engaged",
            "attempt": 0,
            "patched": False,
        }
    )

    return fallback_targets


def test_failover_sequence_escalates_to_rstar_after_kimicho(tmp_path, monkeypatch):
    """Crown → Kimi-cho → Kimi 2 → rStar chain preserves context across retries."""

    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", "2")
    importlib.reload(bo)

    invocation_log = tmp_path / "invocations.json"
    configure_invocation_log(monkeypatch, invocation_log)

    component_name = "demo"
    fallback_targets = simulate_handshake_failure(
        monkeypatch, component_name, tmp_path / "logs"
    )
    assert fallback_targets == ["https://huggingfacc.com/k2coder"]

    config_path = tmp_path / "razar_ai_agents.json"
    config_path.write_text(
        json.dumps(
            {
                "active": "Kimi2",
                "agents": [
                    {"name": "Kimi2"},
                    {"name": "rStar"},
                ],
            }
        )
    )
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", config_path)
    monkeypatch.setattr(bo.ai_invoker, "AGENT_CONFIG_PATH", config_path)

    contexts: list[dict | None] = []
    attempt_agents: list[str] = []

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        contexts.append(context)
        current = json.loads(config_path.read_text())["active"]
        attempt_agents.append(current.lower())
        return current.lower() == "rstar"

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component_cfg = {"name": component_name, "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, attempts_used, _ = bo._retry_with_ai(
        component_name, component_cfg, "boom", 3, failure_tracker
    )

    assert proc is not None
    assert attempts_used == 3
    assert attempt_agents == ["kimi2", "kimi2", "rstar"]
    assert failure_tracker[component_name] == 0
    assert len(contexts) == 3
    for ctx in contexts:
        assert ctx is not None

    first_history = [
        (entry.get("event"), entry.get("agent")) for entry in contexts[0]["history"]
    ]
    assert first_history[:2] == [("handshake", "crown"), ("fallback", "kimicho")]

    final_history = contexts[-1]["history"]
    final_events = [(entry.get("event"), entry.get("agent")) for entry in final_history]
    assert final_events[:2] == [("handshake", "crown"), ("fallback", "kimicho")]
    assert ("escalation", "rstar") in final_events
    assert any(event == "attempt" and agent == "kimi2" for event, agent in final_events)
    assert any(
        entry.get("status") == "failure" and entry.get("agent") == "kimi2"
        for entry in final_history
    )
    full_history = razar_logging.load_invocation_history(component_name)
    assert any(
        entry.get("status") == "success" and entry.get("agent") == "rstar"
        for entry in full_history
    )
    assert any(
        entry.get("event") == "attempt" and entry.get("agent") == "rstar"
        for entry in full_history
    )


def test_failover_sequence_respects_custom_order_and_threshold(tmp_path, monkeypatch):
    """Custom agent order and threshold escalate immediately after Kimi-cho."""

    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", "1")
    importlib.reload(bo)

    invocation_log = tmp_path / "invocations.json"
    configure_invocation_log(monkeypatch, invocation_log)

    component_name = "demo"
    fallback_targets = simulate_handshake_failure(
        monkeypatch, component_name, tmp_path / "logs"
    )
    assert fallback_targets == ["https://huggingfacc.com/k2coder"]

    config_path = tmp_path / "razar_ai_agents.json"
    config_path.write_text(
        json.dumps(
            {
                "active": "rStar",
                "agents": [
                    {"name": "rStar"},
                    {"name": "Kimi2"},
                ],
            }
        )
    )
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", config_path)
    monkeypatch.setattr(bo.ai_invoker, "AGENT_CONFIG_PATH", config_path)

    contexts: list[dict | None] = []
    attempt_agents: list[str] = []

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        contexts.append(context)
        current = json.loads(config_path.read_text())["active"]
        attempt_agents.append(current.lower())
        return current.lower() == "kimi2"

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component_cfg = {"name": component_name, "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, attempts_used, _ = bo._retry_with_ai(
        component_name, component_cfg, "boom", 2, failure_tracker
    )

    assert proc is not None
    assert attempts_used == 2
    assert attempt_agents == ["rstar", "kimi2"]
    assert failure_tracker[component_name] == 0
    assert len(contexts) == 2
    for ctx in contexts:
        assert ctx is not None

    first_history = [
        (entry.get("event"), entry.get("agent")) for entry in contexts[0]["history"]
    ]
    assert first_history[:2] == [("handshake", "crown"), ("fallback", "kimicho")]

    final_history = contexts[-1]["history"]
    final_events = [(entry.get("event"), entry.get("agent")) for entry in final_history]
    assert final_events[:2] == [("handshake", "crown"), ("fallback", "kimicho")]
    assert any(event == "attempt" and agent == "rstar" for event, agent in final_events)
    assert ("escalation", "kimi2") in final_events
    assert any(
        entry.get("status") == "failure" and entry.get("agent") == "rstar"
        for entry in final_history
    )
    full_history = razar_logging.load_invocation_history(component_name)
    assert any(
        entry.get("status") == "success" and entry.get("agent") == "kimi2"
        for entry in full_history
    )
    assert any(
        entry.get("event") == "attempt" and entry.get("agent") == "kimi2"
        for entry in full_history
    )
