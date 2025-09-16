from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import pytest

import razar.bootstrap_utils as bootstrap_utils
import razar.utils.logging as razar_logging
import tests.conftest as conftest_module

conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))


class DummyProcess(SimpleNamespace):
    """Minimal process stub returned by the launch helper."""

    returncode = 0

    def terminate(self) -> None:  # pragma: no cover - trivial helper
        pass

    def wait(self) -> None:  # pragma: no cover - trivial helper
        pass


@pytest.fixture
def boot_orchestrator(monkeypatch: pytest.MonkeyPatch):
    """Reload the boot orchestrator with a low escalation threshold."""

    import razar.boot_orchestrator as bo

    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", "2")
    return importlib.reload(bo)


@pytest.fixture
def invocation_log(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect invocation history writes to an isolated log file."""

    log_path = tmp_path / "razar_invocations.jsonl"
    monkeypatch.setattr(razar_logging, "INVOCATION_LOG_PATH", log_path)
    monkeypatch.setattr(razar_logging, "_LEGACY_CONVERTED", False)
    return log_path


@pytest.fixture
def logs_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, boot_orchestrator):
    """Ensure log output stays within the temporary directory."""

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(boot_orchestrator, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(bootstrap_utils, "LOGS_DIR", logs_dir)
    return logs_dir


@pytest.fixture
def simulate_handshake(
    monkeypatch: pytest.MonkeyPatch,
    boot_orchestrator,
    logs_directory: Path,
    invocation_log: Path,
) -> Callable[[str], list[str]]:
    """Return a callable that forces the Crown handshake fallback."""

    async def failing_handshake(_: str) -> None:
        raise RuntimeError("crown offline")

    def _simulate(component: str) -> list[str]:
        fallback_targets: list[str] = []

        def fake_init(endpoint: str) -> None:
            fallback_targets.append(endpoint)

        monkeypatch.setattr(
            boot_orchestrator.crown_handshake,
            "perform",
            failing_handshake,
        )
        monkeypatch.setattr(boot_orchestrator, "init_kimicho", fake_init)
        monkeypatch.setattr(
            boot_orchestrator,
            "_persist_handshake",
            lambda response: None,
        )
        monkeypatch.setattr(
            boot_orchestrator,
            "_ensure_glm4v",
            lambda capabilities: None,
        )
        monkeypatch.setattr(
            boot_orchestrator,
            "_emit_event",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            boot_orchestrator.mission_logger,
            "log_event",
            lambda *args, **kwargs: None,
        )

        with pytest.raises(RuntimeError, match="CROWN handshake failed"):
            boot_orchestrator._perform_handshake([{"name": component}])

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

    return _simulate


@pytest.fixture
def agent_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, boot_orchestrator
) -> Path:
    """Create a mixed-case agent roster for the failover chain."""

    monkeypatch.setenv("KIMI2_API_KEY", "dummy-kimi2-token")
    monkeypatch.setenv("AIRSTAR_API_KEY", "dummy-airstar-token")
    monkeypatch.setenv("RSTAR_API_KEY", "dummy-rstar-token")
    config_path = tmp_path / "config" / "razar_ai_agents.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "active": "K2 Coder",
                "agents": [
                    {"name": "K2 Coder"},
                    {"name": "Air Star"},
                    {"name": "rStar"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(boot_orchestrator, "AGENT_CONFIG_PATH", config_path)
    monkeypatch.setattr(boot_orchestrator.ai_invoker, "AGENT_CONFIG_PATH", config_path)
    boot_orchestrator.ai_invoker.invalidate_agent_config_cache(config_path)
    return config_path


@pytest.fixture
def stubbed_handover(
    monkeypatch: pytest.MonkeyPatch, agent_config: Path, boot_orchestrator
):
    """Track handover attempts and emulate progressive agent success."""

    contexts: list[dict | None] = []
    invoked_agents: list[str] = []
    use_opencode_flags: list[bool] = []

    def fake_handover(
        component: str,
        error: str,
        *,
        context: dict | None = None,
        use_opencode: bool = False,
    ) -> bool:
        contexts.append(context)
        use_opencode_flags.append(use_opencode)
        current = json.loads(agent_config.read_text()).get("active", "")
        invoked_agents.append(current.lower())
        return current.lower() == "rstar"

    monkeypatch.setattr(boot_orchestrator.ai_invoker, "handover", fake_handover)
    return {
        "contexts": contexts,
        "agents": invoked_agents,
        "use_opencode": use_opencode_flags,
    }


@pytest.fixture
def stubbed_component_controls(monkeypatch: pytest.MonkeyPatch, boot_orchestrator):
    """Avoid launching real subprocesses or external probes."""

    monkeypatch.setattr(
        boot_orchestrator,
        "launch_component",
        lambda comp: DummyProcess(),
    )
    monkeypatch.setattr(
        boot_orchestrator,
        "_execute_health_probe",
        lambda component: True,
    )
    monkeypatch.setattr(
        boot_orchestrator.health_checks,
        "run",
        lambda name: True,
    )


def test_razar_failover_chain_escalates_through_air_star_to_rstar(
    boot_orchestrator,
    simulate_handshake: Callable[[str], list[str]],
    stubbed_handover,
    stubbed_component_controls,
    agent_config: Path,
):
    """Crown → Kimi-cho → K2 Coder → Air Star → rStar propagates history."""

    component_name = "demo-mixed-case"
    fallback_targets = simulate_handshake(component_name)
    assert fallback_targets == ["https://huggingfacc.com/k2coder"]

    failure_tracker: dict[str, int] = {}
    component_def = {"name": component_name, "command": ["echo", "hi"]}
    process, attempts_used, _ = boot_orchestrator._retry_with_ai(
        component_name,
        component_def,
        "boom",
        5,
        failure_tracker,
    )

    assert process is not None
    assert attempts_used == 5
    assert failure_tracker[component_name] == 0

    contexts = stubbed_handover["contexts"]
    assert len(contexts) == 5
    assert all(context is not None for context in contexts)

    agents = stubbed_handover["agents"]
    assert agents == ["k2 coder", "k2 coder", "air star", "air star", "rstar"]
    assert all(flag is False for flag in stubbed_handover["use_opencode"])

    first_history = [
        (entry.get("event"), entry.get("agent"))
        for entry in contexts[0]["history"]
    ]
    assert first_history[:2] == [("handshake", "crown"), ("fallback", "kimicho")]

    final_history = contexts[-1]["history"]
    final_events = [(entry.get("event"), entry.get("agent")) for entry in final_history]
    assert ("escalation", "air star") in final_events
    assert ("escalation", "rstar") in final_events
    assert any(
        event == "attempt" and agent == "k2 coder"
        for event, agent in final_events
    )
    assert any(
        event == "attempt" and agent == "air star"
        for event, agent in final_events
    )
    assert any(
        entry.get("status") == "failure" and entry.get("agent") == "k2 coder"
        for entry in final_history
    )
    assert any(
        entry.get("status") == "failure" and entry.get("agent") == "air star"
        for entry in final_history
    )

    full_history = razar_logging.load_invocation_history(component_name)
    assert any(
        entry.get("status") == "failure" and entry.get("agent") == "air star"
        for entry in full_history
    )
    assert any(
        entry.get("event") == "attempt" and entry.get("agent") == "rstar"
        for entry in full_history
    )
    assert any(
        entry.get("status") == "success" and entry.get("agent") == "rstar"
        for entry in full_history
    )

    final_config = json.loads(agent_config.read_text())
    assert final_config.get("active") == "rStar"
