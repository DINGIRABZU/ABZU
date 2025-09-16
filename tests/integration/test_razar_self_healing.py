import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict

import pytest

import tests.conftest as conftest_module

conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))

COMPONENT_NAME = "demo-self-heal-service"


@pytest.fixture
def boot_orchestrator(monkeypatch: pytest.MonkeyPatch):
    """Reload the boot orchestrator with a deterministic escalation threshold."""

    monkeypatch.setenv("RAZAR_RSTAR_THRESHOLD", "1")
    monkeypatch.setenv("RAZAR_HEALTH_PROBE_INTERVAL", "0")
    import razar.boot_orchestrator as bo

    return importlib.reload(bo)


@pytest.fixture
def logs_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, boot_orchestrator
) -> Path:
    """Redirect runtime artifacts to a temporary directory."""

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    history = logs_dir / "razar_boot_history.json"
    state = logs_dir / "razar_state.json"
    long_task = logs_dir / "razar_long_task.json"
    alerts_dir = logs_dir / "alerts"

    monkeypatch.setattr(boot_orchestrator, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(boot_orchestrator, "HISTORY_FILE", history)
    monkeypatch.setattr(boot_orchestrator, "STATE_FILE", state)
    monkeypatch.setattr(boot_orchestrator, "LONG_TASK_LOG_PATH", long_task)
    monkeypatch.setattr(boot_orchestrator, "MONITORING_ALERTS_DIR", alerts_dir)

    import razar.bootstrap_utils as bootstrap_utils
    import razar.utils.logging as razar_logging

    monkeypatch.setattr(bootstrap_utils, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(bootstrap_utils, "HISTORY_FILE", history)
    monkeypatch.setattr(bootstrap_utils, "STATE_FILE", state)
    monkeypatch.setattr(
        bootstrap_utils,
        "PATCH_LOG_PATH",
        logs_dir / "razar_ai_patches.json",
    )

    monkeypatch.setattr(razar_logging, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(
        razar_logging, "INVOCATION_LOG_PATH", logs_dir / "razar_ai_invocations.json"
    )
    monkeypatch.setattr(razar_logging, "_LEGACY_CONVERTED", True)

    return logs_dir


@pytest.fixture
def agent_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    boot_orchestrator,
    logs_directory: Path,
) -> Path:
    """Create a remote agent roster and point the orchestrator to it."""

    monkeypatch.setenv("KIMI2_API_KEY", "dummy-k2")
    monkeypatch.setenv("AIRSTAR_API_KEY", "dummy-air")
    monkeypatch.setenv("RSTAR_API_KEY", "dummy-r")

    config_path = tmp_path / "config" / "razar_ai_agents.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "active": "Kimi2",
                "agents": [
                    {"name": "Kimi2"},
                    {"name": "AirStar"},
                    {"name": "RStar"},
                ],
            }
        ),
        encoding="utf-8",
    )

    backup_path = config_path.with_suffix(".bak")

    monkeypatch.setattr(boot_orchestrator, "AGENT_CONFIG_PATH", config_path)
    monkeypatch.setattr(boot_orchestrator, "AGENT_CONFIG_BACKUP_PATH", backup_path)
    monkeypatch.setattr(boot_orchestrator.ai_invoker, "AGENT_CONFIG_PATH", config_path)
    boot_orchestrator.ai_invoker.invalidate_agent_config_cache(config_path)

    return config_path


@pytest.fixture
def boot_config(tmp_path: Path) -> Path:
    """Write a minimal boot configuration consumed by the orchestrator."""

    config_path = tmp_path / "boot_config.json"
    config_path.write_text(
        json.dumps(
            {
                "components": [
                    {
                        "name": COMPONENT_NAME,
                        "command": ["python", "-c", "print('noop')"],
                        "health_check": ["python", "-c", "print('noop')"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return config_path


@pytest.fixture
def scenario_runner(
    monkeypatch: pytest.MonkeyPatch,
    boot_orchestrator,
    logs_directory: Path,
    agent_config: Path,
    boot_config: Path,
) -> Callable[[int], Dict[str, Any]]:
    """Return a callable that executes a failing boot cycle and captures artifacts."""

    def _run(remote_attempts: int = 3) -> Dict[str, Any]:
        alerts: list[Dict[str, Any]] = []
        quarantine: list[Dict[str, Any]] = []
        handovers: list[Dict[str, Any]] = []
        rollback_snapshots: list[Dict[str, Any]] = []
        events: list[Dict[str, Any]] = []
        log_entries: list[Dict[str, Any]] = []

        original_rollback = boot_orchestrator.rollback_to_safe_defaults

        def tracked_rollback() -> None:
            rollback_snapshots.append(json.loads(agent_config.read_text()))
            original_rollback()

        monkeypatch.setattr(
            boot_orchestrator, "rollback_to_safe_defaults", tracked_rollback
        )

        original_append = boot_orchestrator.append_invocation_event

        def tracked_append(entry: Dict[str, Any]) -> Dict[str, Any]:
            record = original_append(entry)
            events.append(record)
            return record

        monkeypatch.setattr(
            boot_orchestrator, "append_invocation_event", tracked_append
        )

        original_log_invocation = boot_orchestrator.log_invocation

        def tracked_log_invocation(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            record = original_log_invocation(*args, **kwargs)
            log_entries.append(record)
            return record

        monkeypatch.setattr(boot_orchestrator, "log_invocation", tracked_log_invocation)

        def fake_send_monitoring_alert(
            message: str, *, severity: str, context: Dict[str, Any] | None = None
        ) -> None:
            alerts.append(
                {"message": message, "severity": severity, "context": context}
            )

        monkeypatch.setattr(
            boot_orchestrator, "send_monitoring_alert", fake_send_monitoring_alert
        )

        def fake_quarantine(component: Dict[str, Any], reason: str) -> None:
            quarantine.append({"name": component.get("name"), "reason": reason})

        monkeypatch.setattr(boot_orchestrator, "quarantine_component", fake_quarantine)

        def failing_launch(_: Dict[str, Any]):
            raise RuntimeError("simulated launch failure")

        monkeypatch.setattr(boot_orchestrator, "launch_component", failing_launch)

        monkeypatch.setattr(boot_orchestrator.metrics, "init_metrics", lambda: None)
        monkeypatch.setattr(
            boot_orchestrator.metrics, "observe_retry_duration", lambda *_, **__: None
        )
        monkeypatch.setattr(boot_orchestrator.doc_sync, "sync_docs", lambda: None)
        monkeypatch.setattr(
            boot_orchestrator.mission_logger, "log_event", lambda *_, **__: None
        )
        monkeypatch.setattr(boot_orchestrator, "launch_required_agents", lambda: None)
        monkeypatch.setattr(boot_orchestrator, "load_rust_components", lambda: None)
        monkeypatch.setattr(boot_orchestrator, "_emit_event", lambda *_, **__: None)
        monkeypatch.setattr(
            boot_orchestrator,
            "_perform_handshake",
            lambda _components: SimpleNamespace(capabilities=[], downtime=0),
        )
        monkeypatch.setattr(
            boot_orchestrator.logging, "basicConfig", lambda *_, **__: None
        )
        monkeypatch.setattr(boot_orchestrator.health_checks, "run", lambda _: False)

        def failing_handover(
            component: str,
            error: str,
            *,
            context: Dict[str, Any] | None = None,
            use_opencode: bool = False,
        ) -> bool:
            active = json.loads(agent_config.read_text()).get("active")
            handovers.append(
                {
                    "component": component,
                    "error": error,
                    "active": active,
                    "use_opencode": use_opencode,
                    "context": context,
                }
            )
            return False

        monkeypatch.setattr(boot_orchestrator.ai_invoker, "handover", failing_handover)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "razar.boot_orchestrator",
                "--config",
                str(boot_config),
                "--retries",
                "0",
                "--remote-attempts",
                str(remote_attempts),
            ],
        )

        with pytest.raises(SystemExit) as excinfo:
            boot_orchestrator.main()

        return {
            "exit_code": excinfo.value.code,
            "alerts": alerts,
            "quarantine": quarantine,
            "handover_calls": handovers,
            "rollback_snapshots": rollback_snapshots,
            "events": events,
            "log_entries": log_entries,
        }

    return _run


def test_failed_escalations_trigger_rollback_and_restore_config(
    scenario_runner: Callable[[int], Dict[str, Any]], agent_config: Path
) -> None:
    """Exhaust the escalation ladder and confirm the orchestrator rolls back."""

    result = scenario_runner(remote_attempts=3)

    assert result["exit_code"] == 1
    assert result["rollback_snapshots"], "Expected rollback_to_safe_defaults to run"

    pre_rollback_state = result["rollback_snapshots"][0]
    assert pre_rollback_state.get("active") == "RStar"

    final_config = json.loads(agent_config.read_text())
    assert final_config.get("active") == "Kimi2"

    escalation_events = [
        event for event in result["events"] if event.get("event") == "escalation"
    ]
    assert [event.get("agent") for event in escalation_events] == [
        "airstar",
        "rstar",
    ]

    assert result["alerts"], "Expected monitoring alert describing the rollback"
    alert = result["alerts"][0]
    assert alert["severity"] == "critical"
    assert "rolled back" in alert["message"]

    assert result["quarantine"], "Component should be quarantined after failure"
    quarantine_entry = result["quarantine"][0]
    assert quarantine_entry["name"] == COMPONENT_NAME
    assert "simulated launch failure" in quarantine_entry["reason"]


def test_failed_escalations_log_history_before_rollback(
    scenario_runner: Callable[[int], Dict[str, Any]]
) -> None:
    """Verify escalation history is preserved for post-mortem triage."""

    result = scenario_runner(remote_attempts=3)

    handovers = result["handover_calls"]
    assert [call["active"] for call in handovers] == ["Kimi2", "AirStar", "RStar"]

    assert len(handovers) == 3
    second_history = handovers[1]["context"] or {}
    third_history = handovers[2]["context"] or {}

    def _agents_from_history(history: Dict[str, Any]) -> list[str]:
        return [
            entry.get("agent")
            for entry in history.get("history", [])
            if entry.get("event") == "escalation"
        ]

    assert "airstar" in _agents_from_history(second_history)
    assert "rstar" in _agents_from_history(third_history)

    attempts = [entry.get("attempt") for entry in result["log_entries"]]
    assert attempts == [1, 2, 3]

    assert all(call["use_opencode"] is False for call in handovers)
