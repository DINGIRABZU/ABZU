from __future__ import annotations

"""Execute the RAZAR chaos escalation drill.

The drill simulates a boot failure that forces the orchestrator to escalate
through the default Crown → Kimi-cho → K2 Coder → Air Star → rStar ladder.
It runs the retry loop in isolation, confirms the retry duration metric is
observed, snapshots and rolls back the agent roster, and validates that the
Prometheus alert catalog references the published escalation runbook.

Use ``python scripts/razar_chaos_drill.py`` to run the drill locally. Passing
``--dry-run`` keeps the orchestration entirely in an isolated temporary
environment while still exercising the escalation path and health checks.
"""

import argparse
import importlib
import json
import os
import sys
import tempfile
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any, Dict, List, Mapping, Sequence

from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
ALERTS_DIR = PROJECT_ROOT / "monitoring" / "alerts"
RUNBOOK_PATH = "docs/runbooks/razar_escalation.md"


@dataclass(slots=True)
class DrillReport:
    """Summary of the chaos drill execution."""

    component: str
    dry_run: bool
    fallback_targets: List[str]
    escalation_agents: List[str]
    retry_durations: List[Dict[str, float]]
    invocation_events: List[Dict[str, Any]]
    handover_calls: List[Dict[str, Any]]
    handover_logs: List[Dict[str, Any]]
    rollback_snapshots: List[Mapping[str, Any]]
    monitoring_alerts: List[Dict[str, Any]]
    alert_runbooks: Dict[str, List[str]]
    alerts_missing_runbook: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the report."""

        return {
            "component": self.component,
            "dry_run": self.dry_run,
            "fallback_targets": list(self.fallback_targets),
            "escalation_agents": list(self.escalation_agents),
            "retry_durations": list(self.retry_durations),
            "invocation_events": list(self.invocation_events),
            "handover_calls": list(self.handover_calls),
            "handover_logs": list(self.handover_logs),
            "rollback_snapshots": [
                dict(snapshot) for snapshot in self.rollback_snapshots
            ],
            "monitoring_alerts": list(self.monitoring_alerts),
            "alert_runbooks": {
                name: list(values) for name, values in self.alert_runbooks.items()
            },
            "alerts_missing_runbook": list(self.alerts_missing_runbook),
        }


def _collect_alert_runbooks(directory: Path) -> tuple[Dict[str, List[str]], List[str]]:
    """Return runbook references for each alert file in ``directory``."""

    runbooks: Dict[str, List[str]] = {}
    missing: List[str] = []
    if not directory.exists():
        return runbooks, [directory.name]

    for path in sorted(directory.glob("*.yml")):
        references: List[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("runbook:"):
                references.append(stripped.split("runbook:", 1)[1].strip())
        runbooks[path.name] = references
        if all(RUNBOOK_PATH not in ref for ref in references):
            missing.append(path.name)
    return runbooks, missing


def _default_agent_roster() -> Dict[str, Any]:
    """Return the default chaos drill roster with mixed-case agent names."""

    return {
        "active": "K2 Coder",
        "agents": [
            {"name": "K2 Coder"},
            {"name": "Air Star"},
            {"name": "rStar"},
        ],
    }


def _prepare_environment() -> None:
    """Ensure environment variables required by the drill are set."""

    os.environ.setdefault("RAZAR_RSTAR_THRESHOLD", "1")
    os.environ.setdefault("RAZAR_HEALTH_PROBE_INTERVAL", "0")
    os.environ.setdefault("KIMI2_API_KEY", "chaos-dummy-k2")
    os.environ.setdefault("AIRSTAR_API_KEY", "chaos-dummy-air")
    os.environ.setdefault("RSTAR_API_KEY", "chaos-dummy-r")


def _load_modules():
    """Reload RAZAR modules so patched environment variables take effect."""

    import razar.boot_orchestrator as boot_orchestrator
    import razar.bootstrap_utils as bootstrap_utils
    import razar.utils.logging as razar_logging

    return (
        importlib.reload(boot_orchestrator),
        importlib.reload(bootstrap_utils),
        importlib.reload(razar_logging),
    )


def run_chaos_drill(
    *,
    component: str = "razar-chaos-service",
    remote_attempts: int = 3,
    dry_run: bool = False,
) -> DrillReport:
    """Execute the chaos drill and return a :class:`DrillReport`."""

    _prepare_environment()
    boot_orchestrator, bootstrap_utils, razar_logging = _load_modules()

    with tempfile.TemporaryDirectory(prefix="razar-chaos-") as tmpdir:
        temp_root = Path(tmpdir)
        logs_dir = temp_root / "logs"
        alerts_dir = logs_dir / "alerts"
        config_dir = temp_root / "config"
        logs_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)

        history_path = logs_dir / "razar_boot_history.json"
        state_path = logs_dir / "razar_state.json"
        long_task_path = logs_dir / "razar_long_task.json"
        invocation_path = logs_dir / "razar_ai_invocations.json"
        patch_log_path = logs_dir / "razar_ai_patches.json"
        agent_config_path = config_dir / "razar_ai_agents.json"
        agent_config_backup = agent_config_path.with_suffix(".bak")

        agent_config_path.write_text(
            json.dumps(_default_agent_roster(), indent=2),
            encoding="utf-8",
        )

        durations: List[Dict[str, float]] = []
        fallback_targets: List[str] = []
        invocation_events: List[Dict[str, Any]] = []
        handover_calls: List[Dict[str, Any]] = []
        handover_logs: List[Dict[str, Any]] = []
        rollback_snapshots: List[Mapping[str, Any]] = []
        monitoring_alerts: List[Dict[str, Any]] = []

        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(boot_orchestrator, "LOGS_DIR", logs_dir)
            )
            stack.enter_context(
                mock.patch.object(boot_orchestrator, "HISTORY_FILE", history_path)
            )
            stack.enter_context(
                mock.patch.object(boot_orchestrator, "STATE_FILE", state_path)
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "LONG_TASK_LOG_PATH", long_task_path
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "MONITORING_ALERTS_DIR", alerts_dir
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "AGENT_CONFIG_PATH", agent_config_path
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "AGENT_CONFIG_BACKUP_PATH", agent_config_backup
                )
            )
            stack.enter_context(
                mock.patch.object(bootstrap_utils, "LOGS_DIR", logs_dir)
            )
            stack.enter_context(
                mock.patch.object(bootstrap_utils, "HISTORY_FILE", history_path)
            )
            stack.enter_context(
                mock.patch.object(bootstrap_utils, "STATE_FILE", state_path)
            )
            stack.enter_context(
                mock.patch.object(bootstrap_utils, "PATCH_LOG_PATH", patch_log_path)
            )
            stack.enter_context(mock.patch.object(razar_logging, "LOGS_DIR", logs_dir))
            stack.enter_context(
                mock.patch.object(razar_logging, "INVOCATION_LOG_PATH", invocation_path)
            )
            stack.enter_context(
                mock.patch.object(razar_logging, "_LEGACY_CONVERTED", True)
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.ai_invoker,
                    "AGENT_CONFIG_PATH",
                    agent_config_path,
                )
            )

            original_observe = boot_orchestrator.metrics.observe_retry_duration

            def _track_retry_duration(name: str, duration: float) -> None:
                durations.append({"component": name, "duration": duration})
                if callable(original_observe):
                    original_observe(name, duration)

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.metrics,
                    "observe_retry_duration",
                    _track_retry_duration,
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.metrics, "init_metrics", lambda: None
                )
            )
            stack.enter_context(
                mock.patch.object(boot_orchestrator.doc_sync, "sync_docs", lambda: None)
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.mission_logger, "log_event", lambda *_, **__: None
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "_emit_event", lambda *_, **__: None
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "launch_required_agents", lambda: None
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "load_rust_components", lambda: None
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.logging, "basicConfig", lambda *_, **__: None
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.LOGGER, "exception", lambda *_, **__: None
                )
            )

            original_append = boot_orchestrator.append_invocation_event

            def _record_event(entry: Mapping[str, Any]) -> Dict[str, Any]:
                record = original_append(entry)
                invocation_events.append(record)
                return record

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "append_invocation_event", _record_event
                )
            )

            original_log_invocation = boot_orchestrator.log_invocation

            def _record_log_invocation(*args: Any, **kwargs: Any) -> Dict[str, Any]:
                record = original_log_invocation(*args, **kwargs)
                handover_logs.append(record)
                return record

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "log_invocation", _record_log_invocation
                )
            )

            def _failing_launch(_: Mapping[str, Any]) -> None:
                raise RuntimeError("simulated launch failure")

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "launch_component", _failing_launch
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "_execute_health_probe", lambda *_: False
                )
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.health_checks, "run", lambda *_: False
                )
            )

            quarantine_records: List[Dict[str, Any]] = []

            def _record_quarantine(
                component_def: Mapping[str, Any], reason: str
            ) -> None:
                quarantine_records.append(
                    {"name": component_def.get("name", ""), "reason": reason}
                )

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "quarantine_component", _record_quarantine
                )
            )

            original_rollback = boot_orchestrator.rollback_to_safe_defaults

            def _tracked_rollback() -> None:
                try:
                    snapshot = json.loads(agent_config_path.read_text(encoding="utf-8"))
                except Exception:  # pragma: no cover - defensive guard
                    snapshot = {"error": "snapshot_failed"}
                rollback_snapshots.append(snapshot)
                original_rollback()

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "rollback_to_safe_defaults", _tracked_rollback
                )
            )

            def _record_alert(
                message: str,
                *,
                severity: str = "warning",
                context: Mapping[str, Any] | None = None,
            ) -> None:
                payload = {
                    "message": message,
                    "severity": severity,
                    "context": dict(context or {}),
                }
                monitoring_alerts.append(payload)
                alerts_dir.mkdir(parents=True, exist_ok=True)
                stamp = str(int(perf_counter() * 1000))
                alert_path = alerts_dir / f"chaos_{stamp}.json"
                alert_path.write_text(
                    json.dumps(payload, sort_keys=True), encoding="utf-8"
                )

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "send_monitoring_alert", _record_alert
                )
            )

            async def _failing_handshake(_: str) -> None:
                raise RuntimeError("crown offline")

            def _capture_kimicho(endpoint: str) -> None:
                fallback_targets.append(endpoint)

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.crown_handshake, "perform", _failing_handshake
                )
            )
            stack.enter_context(
                mock.patch.object(boot_orchestrator, "init_kimicho", _capture_kimicho)
            )
            stack.enter_context(
                mock.patch.object(boot_orchestrator, "_ensure_glm4v", lambda *_: None)
            )
            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator, "_persist_handshake", lambda *_: None
                )
            )

            boot_orchestrator.ai_invoker.invalidate_agent_config_cache(
                agent_config_path
            )
            boot_orchestrator.metrics.init_metrics()

            boot_orchestrator._snapshot_agent_config()

            try:
                boot_orchestrator._perform_handshake([{"name": component}])
            except RuntimeError:
                boot_orchestrator.append_invocation_event(
                    {
                        "component": component,
                        "event": "handshake",
                        "agent": "crown",
                        "agent_original": "Crown",
                        "error": "crown offline",
                        "patched": False,
                        "attempt": 0,
                    }
                )
                boot_orchestrator.append_invocation_event(
                    {
                        "component": component,
                        "event": "fallback",
                        "agent": "kimicho",
                        "agent_original": "Kimi-cho",
                        "error": "kimicho engaged",
                        "patched": False,
                        "attempt": 0,
                    }
                )
            else:  # pragma: no cover - handshake must fail during drill
                raise RuntimeError("Chaos drill expected Crown handshake to fail")

            def _tracked_handover(
                _component: str,
                _error: str,
                *,
                context: Mapping[str, Any] | None = None,
                use_opencode: bool = False,
            ) -> bool:
                try:
                    current_config = json.loads(
                        agent_config_path.read_text(encoding="utf-8")
                    )
                except Exception:  # pragma: no cover - defensive guard
                    active_agent = ""
                else:
                    active_agent = str(current_config.get("active", "")).lower()
                handover_calls.append(
                    {
                        "component": _component,
                        "error": _error,
                        "active": active_agent,
                        "use_opencode": use_opencode,
                        "context": dict(context or {}),
                    }
                )
                return False

            stack.enter_context(
                mock.patch.object(
                    boot_orchestrator.ai_invoker, "handover", _tracked_handover
                )
            )

            failure_tracker: Dict[str, int] = {}
            escalation_tracker: Dict[str, int] = {}
            registry_lock = Lock()
            component_def = {
                "name": component,
                "command": ["python", "-c", "print('noop')"],
                "health_check": ["python", "-c", "print('noop')"],
            }

            run_start = time.time()
            process, attempts_used, last_error = boot_orchestrator._retry_with_ai(
                component,
                component_def,
                "simulated launch failure",
                remote_attempts,
                failure_tracker,
                escalation_tracker,
                registry_lock,
            )

            if process is not None:  # pragma: no cover - drill expects failure
                process.terminate()
                raise RuntimeError("Chaos drill expected remote escalation to fail")

            boot_orchestrator.quarantine_component(component_def, last_error)

            boot_orchestrator.rollback_to_safe_defaults()
            boot_orchestrator.send_monitoring_alert(
                "Boot sequence halted; configuration rolled back to safe defaults",
                severity="critical",
                context={
                    "component": component,
                    "dry_run": dry_run,
                    "attempts": attempts_used,
                },
            )

            history_payload: Dict[str, Any] = {}
            if history_path.exists():
                try:
                    history_payload = json.loads(
                        history_path.read_text(encoding="utf-8")
                    )
                except json.JSONDecodeError:  # pragma: no cover - defensive guard
                    history_payload = {}

            run_metrics = {
                "components": [
                    {
                        "name": component,
                        "attempts": attempts_used,
                        "success": False,
                    }
                ],
                "timestamp": time.time(),
            }

            boot_orchestrator.finalize_metrics(
                run_metrics,
                history_payload,
                failure_tracker,
                run_start,
            )

        escalation_agents = [attempt.get("active", "") for attempt in handover_calls]
        runbooks, missing_runbooks = _collect_alert_runbooks(ALERTS_DIR)

        return DrillReport(
            component=component,
            dry_run=dry_run,
            fallback_targets=fallback_targets,
            escalation_agents=escalation_agents,
            retry_durations=durations,
            invocation_events=invocation_events,
            handover_calls=handover_calls,
            handover_logs=handover_logs,
            rollback_snapshots=rollback_snapshots,
            monitoring_alerts=monitoring_alerts,
            alert_runbooks=runbooks,
            alerts_missing_runbook=missing_runbooks,
        )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--component",
        default="razar-chaos-service",
        help="Component name used when simulating the failure sequence.",
    )
    parser.add_argument(
        "--remote-attempts",
        type=int,
        default=3,
        help="Maximum remote retries during the drill (default: 3).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the drill in isolation without touching live artifacts.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run_chaos_drill(
        component=args.component,
        remote_attempts=args.remote_attempts,
        dry_run=args.dry_run,
    )

    payload = report.to_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))

    errors: List[str] = []
    if not payload["retry_durations"]:
        errors.append("metrics.observe_retry_duration was not invoked")
    if payload["alerts_missing_runbook"]:
        missing = ", ".join(payload["alerts_missing_runbook"])
        errors.append(f"alerts missing escalation runbook reference: {missing}")

    if errors:
        for err in errors:
            print(err, flush=True)
        return 1
    return 0


__all__ = ["run_chaos_drill", "DrillReport"]


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
