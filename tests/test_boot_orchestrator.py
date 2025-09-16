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

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ):
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


def test_escalation_respects_module_threshold(tmp_path, monkeypatch):
    """Escalates after exactly :data:`bo.RSTAR_THRESHOLD` failures."""

    monkeypatch.delenv("RAZAR_RSTAR_THRESHOLD", raising=False)
    importlib.reload(bo)
    monkeypatch.setattr(bo, "RSTAR_THRESHOLD", 4)

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

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ):
        current = json.loads(cfg_path.read_text())["active"]
        attempts.append(current)
        return current == "rstar"

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    max_attempts = bo.RSTAR_THRESHOLD + 1
    proc, used_attempts, err = bo._retry_with_ai(
        "demo", component, "boom", max_attempts, failure_tracker
    )

    assert proc is not None and used_attempts == max_attempts
    assert attempts == ["demo_agent"] * bo.RSTAR_THRESHOLD + ["rstar"]
    log = json.loads(inv_log.read_text())
    escalations = [e.get("agent") for e in log if e.get("event") == "escalation"]
    assert escalations == ["rstar"]


@pytest.mark.parametrize("threshold", [1, 2])
def test_agent_escalation_sequence(tmp_path, monkeypatch, threshold):
    """Escalates through the chain while validating context history."""

    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", str(threshold))
    importlib.reload(bo)

    inv_log = tmp_path / "invocations.json"
    cfg_path = tmp_path / "agents.json"
    chain = ["demo_agent", "kimi2", "airstar", "rstar"]
    cfg_path.write_text(
        json.dumps(
            {
                "active": chain[0],
                "agents": [{"name": name} for name in chain],
            }
        )
    )
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", cfg_path)

    original_build_failure_context = bo.build_failure_context

    def full_history_context(component: str, limit: int = 5) -> dict:
        """Increase history window to observe every escalation in the test."""

        extended_limit = max(limit, threshold * len(chain) * 2)
        return original_build_failure_context(component, limit=extended_limit)

    monkeypatch.setattr(bo, "build_failure_context", full_history_context)

    contexts: list[dict] = []
    sequence: list[str] = []
    call_count = 0
    fail_limit = threshold * (len(chain) - 1)

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        nonlocal call_count
        contexts.append(context or {})
        current = json.loads(cfg_path.read_text())["active"].lower()
        sequence.append(current)
        call_count += 1
        return call_count > fail_limit

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, used_attempts, err = bo._retry_with_ai(
        "demo", component, "boom", fail_limit + 1, failure_tracker
    )

    assert proc is not None and used_attempts == fail_limit + 1

    expected_sequence: list[str] = []
    for agent in chain[:-1]:
        expected_sequence.extend([agent] * threshold)
    expected_sequence.append(chain[-1])

    assert sequence == expected_sequence
    assert len(contexts) == len(sequence)
    assert contexts[0] == {}

    for idx, context in enumerate(contexts):
        history = context.get("history", [])
        attempt_agents = [
            entry.get("agent")
            for entry in history
            if entry.get("event") == "attempt" and entry.get("agent")
        ]
        assert attempt_agents == expected_sequence[:idx]

        expected_escalations = [
            chain[i] for i in range(1, len(chain)) if threshold * i <= idx
        ]
        escalation_agents = [
            entry.get("agent")
            for entry in history
            if entry.get("event") == "escalation"
        ]
        assert escalation_agents == expected_escalations

    log = json.loads(inv_log.read_text())
    escalations = [e.get("agent") for e in log if e.get("event") == "escalation"]
    assert escalations == chain[1:]


def test_mixed_case_agent_config(tmp_path, monkeypatch):
    """Handles mixed-case agent names from configuration files."""
    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", "1")
    importlib.reload(bo)

    inv_log = tmp_path / "invocations.json"
    cfg_path = tmp_path / "agents.json"
    cfg_path.write_text(
        json.dumps(
            {
                "active": "KiMi2",
                "agents": [
                    {"name": "KiMi2"},
                    {"name": "AirStar"},
                    {"name": "RStar"},
                ],
            }
        )
    )
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", cfg_path)

    attempts: list[str] = []

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        current = json.loads(cfg_path.read_text())["active"]
        attempts.append(current.lower())
        return current.lower() == "rstar"

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, used_attempts, err = bo._retry_with_ai(
        "demo", component, "boom", 3, failure_tracker
    )

    assert proc is not None and used_attempts == 3
    assert attempts == ["kimi2", "airstar", "rstar"]
    log = json.loads(inv_log.read_text())
    attempt_agents = [e.get("agent") for e in log if e.get("event") == "attempt"]
    assert attempt_agents == ["kimi2", "airstar", "rstar"]
    attempt_originals = [
        e.get("agent_original") for e in log if e.get("event") == "attempt"
    ]
    assert attempt_originals == ["KiMi2", "AirStar", "RStar"]
    escalations = [
        (e.get("agent"), e.get("agent_original"))
        for e in log
        if e.get("event") == "escalation"
    ]
    assert escalations == [("airstar", "AirStar"), ("rstar", "RStar")]


def test_custom_agent_failover_chain(tmp_path, monkeypatch):
    """Respects the agent order defined in a custom configuration file."""
    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", "1")
    importlib.reload(bo)

    inv_log = tmp_path / "invocations.json"
    cfg_path = tmp_path / "razar_ai_agents.json"
    cfg_path.write_text(
        json.dumps(
            {
                "active": "Scout",
                "agents": [
                    {"name": "Scout"},
                    {"name": "Sentinel"},
                    {"name": "Guardian"},
                ],
            }
        )
    )
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", cfg_path)

    attempts: list[str] = []

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        current = json.loads(cfg_path.read_text())["active"]
        attempts.append(current.lower())
        return current.lower() == "guardian"

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, used_attempts, err = bo._retry_with_ai(
        "demo", component, "boom", 5, failure_tracker
    )

    assert proc is not None and used_attempts == 3
    assert attempts == ["scout", "sentinel", "guardian"]
    log = json.loads(inv_log.read_text())
    escalations = [e.get("agent") for e in log if e.get("event") == "escalation"]
    assert escalations == ["sentinel", "guardian"]


def test_retry_with_ai_passes_failure_context(tmp_path, monkeypatch):
    """`_retry_with_ai` forwards the context returned by `build_failure_context`."""

    monkeypatch.delenv("RAZAR_RSTAR_THRESHOLD", raising=False)
    importlib.reload(bo)

    inv_log = tmp_path / "invocations.json"
    cfg_path = tmp_path / "agents.json"
    cfg_path.write_text(
        json.dumps(
            {
                "active": "demo_agent",
                "agents": [
                    {"name": "demo_agent"},
                ],
            }
        )
    )
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", cfg_path)

    sentinel_context = {"history": ["sentinel"]}
    context_calls: list[str] = []

    def fake_build_failure_context(component: str) -> dict:
        context_calls.append(component)
        return sentinel_context

    contexts: list[dict | None] = []

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        contexts.append(context)
        return True

    monkeypatch.setattr(bo, "build_failure_context", fake_build_failure_context)
    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, used_attempts, err = bo._retry_with_ai(
        "demo", component, "boom", 1, failure_tracker
    )

    assert proc is not None and used_attempts == 1
    assert context_calls == ["demo"]
    assert contexts == [sentinel_context]


def test_context_includes_history(tmp_path, monkeypatch):
    """Final agent receives history of previous failed attempts."""
    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", "1")
    importlib.reload(bo)

    inv_log = tmp_path / "invocations.json"
    cfg_path = tmp_path / "agents.json"
    cfg_path.write_text(
        json.dumps(
            {
                "active": "demo_agent",
                "agents": [
                    {"name": "demo_agent"},
                    {"name": "kimi2"},
                    {"name": "airstar"},
                    {"name": "rstar"},
                ],
            }
        )
    )
    monkeypatch.setattr(bo, "INVOCATION_LOG_PATH", inv_log)
    monkeypatch.setattr(bo, "AGENT_CONFIG_PATH", cfg_path)

    contexts: list[dict | None] = []

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        contexts.append(context)
        current = json.loads(cfg_path.read_text())["active"]
        return current == "rstar"

    monkeypatch.setattr(bo.ai_invoker, "handover", fake_handover)
    monkeypatch.setattr(bo.health_checks, "run", lambda name: True)
    monkeypatch.setattr(bo, "launch_component", lambda comp: DummyProc())

    component = {"name": "demo", "command": ["echo", "hi"]}
    failure_tracker: dict[str, int] = {}
    proc, used_attempts, err = bo._retry_with_ai(
        "demo", component, "boom", 4, failure_tracker
    )

    assert proc is not None and used_attempts == 4
    assert len(contexts) == 4
    # Final context includes history from earlier failed attempts
    final_history = contexts[3]["history"]
    attempt_agents = [
        entry["agent"]
        for entry in final_history
        if entry.get("event") == "attempt" and entry.get("agent")
    ]
    assert attempt_agents[-2:] == ["kimi2", "airstar"]
