"""Simple boot orchestrator reading a JSON component configuration.

The orchestrator launches components from basic to complex as defined in the
configuration file. A health check hook runs after each launch and any failure
halts the boot sequence. Failed components are quarantined and skipped on
subsequent runs.
"""

from __future__ import annotations

__version__ = "0.3.0"

import argparse
import asyncio
import json
import logging
import os
import smtplib
import subprocess
import threading
import time
from dataclasses import asdict
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - tracing optional
    from opentelemetry import trace

    _tracer = trace.get_tracer(__name__)
except Exception:  # pragma: no cover - tracing optional
    _tracer = None

try:  # pragma: no cover - Rust crates optional
    from memory.bundle import MemoryBundle
    from neoabzu_core import evaluate_py as _core_eval

    _memory_bundle = MemoryBundle()
except Exception:  # pragma: no cover - Rust crates optional
    _memory_bundle = None
    _core_eval = None

try:  # pragma: no cover - kimicho optional
    from neoabzu_kimicho import init_kimicho  # PyO3 bindings
except Exception:  # pragma: no cover - kimicho optional
    init_kimicho = None

try:  # pragma: no cover - requests optional
    import requests
except Exception:  # pragma: no cover - requests optional
    requests = None

from . import (
    ai_invoker,
    crown_handshake,
    doc_sync,
    health_checks,
    metrics,
    mission_logger,
)
from .bootstrap_utils import (
    HISTORY_FILE,
    LOGS_DIR,
    MAX_MISSION_BRIEFS,
    STATE_FILE,
)
from .utils.logging import (
    append_invocation_event,
    load_invocation_history,
    log_invocation,
)
from .crown_handshake import CrownResponse
from .quarantine_manager import is_quarantined, quarantine_component
from agents.nazarick.service_launcher import launch_required_agents

LOGGER = logging.getLogger("razar.boot_orchestrator")


def _env_float(name: str, default: float) -> float:
    """Return float from environment variable ``name`` with fallback."""

    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        LOGGER.warning("Invalid %s=%s; using default %s", name, value, default)
        return default


def _env_int(name: str, default: int) -> int:
    """Return int from environment variable ``name`` with fallback."""

    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        LOGGER.warning("Invalid %s=%s; using default %s", name, value, default)
        return default


HEALTH_PROBE_INTERVAL = _env_float("RAZAR_HEALTH_PROBE_INTERVAL", 60.0)
ESCALATION_WARNING_THRESHOLD = _env_int("RAZAR_ESCALATION_WARNING_THRESHOLD", 3)
ALERT_WEBHOOK_URL = os.getenv("RAZAR_ALERT_WEBHOOK")
ALERT_EMAIL_RECIPIENT = os.getenv("RAZAR_ALERT_EMAIL")
ALERT_EMAIL_SENDER = os.getenv("RAZAR_ALERT_EMAIL_SENDER", "razar@localhost")
ALERT_EMAIL_SMTP = os.getenv("RAZAR_ALERT_EMAIL_SMTP", "localhost")
ALERT_EMAIL_PORT = _env_int("RAZAR_ALERT_EMAIL_PORT", 25)
MONITORING_ALERTS_DIR = Path(__file__).resolve().parents[1] / "monitoring" / "alerts"
STATE_FILE_LOCK = threading.RLock()


def load_rust_components() -> None:
    """Initialize Rust memory bundle and core engine if available."""
    if _memory_bundle is None or _core_eval is None:
        LOGGER.debug("Rust components unavailable")
        return
    if _tracer:
        with _tracer.start_as_current_span("razar.rust_boot"):
            _memory_bundle.initialize()
            _core_eval("(\\x.x)")
    else:
        _memory_bundle.initialize()
        _core_eval("(\\x.x)")


LONG_TASK_LOG_PATH = LOGS_DIR / "razar_long_task.json"
AGENT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "razar_ai_agents.json"
)
AGENT_CONFIG_BACKUP_PATH = AGENT_CONFIG_PATH.with_suffix(".bak")
RSTAR_THRESHOLD = _env_int("RAZAR_RSTAR_THRESHOLD", 9)


def load_history() -> Dict[str, Any]:
    """Return persisted boot history data."""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except json.JSONDecodeError:  # pragma: no cover - corrupt file
            LOGGER.warning("History file corrupt, starting fresh")
    return {"history": [], "best_sequence": None, "component_failures": {}}


def save_history(data: Dict[str, Any]) -> None:
    """Persist ``data`` to the history file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(data, indent=2))


def finalize_metrics(
    run_metrics: Dict[str, Any],
    history: Dict[str, Any],
    failure_counts: Dict[str, int],
    start_time: float,
) -> None:
    """Compute run statistics and update ``history``."""
    total = len(run_metrics["components"])
    successes = sum(1 for c in run_metrics["components"] if c["success"])
    run_metrics["success_rate"] = successes / total if total else 0.0
    run_metrics["total_time"] = time.time() - start_time

    history.setdefault("history", []).append(run_metrics)

    best = history.get("best_sequence")
    if (
        not best
        or run_metrics["success_rate"] > best.get("success_rate", 0)
        or (
            run_metrics["success_rate"] == best.get("success_rate", 0)
            and run_metrics["total_time"] < best.get("total_time", float("inf"))
        )
    ):
        history["best_sequence"] = {
            "components": [
                c["name"] for c in run_metrics["components"] if c["success"]
            ],
            "success_rate": run_metrics["success_rate"],
            "total_time": run_metrics["total_time"],
            "timestamp": run_metrics["timestamp"],
        }

    history["component_failures"] = failure_counts
    save_history(history)


def _persist_handshake(response: Optional[CrownResponse]) -> None:
    """Write handshake ``response`` details to ``STATE_FILE``."""
    data: Dict[str, Any] = {}
    with STATE_FILE_LOCK:
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
            except json.JSONDecodeError:
                data = {}
        if response is not None:
            data["capabilities"] = response.capabilities
            data["downtime"] = response.downtime
            data["handshake"] = {
                "acknowledgement": response.acknowledgement,
                "capabilities": response.capabilities,
                "downtime": response.downtime,
            }
        else:
            data.setdefault("capabilities", [])
            data.setdefault("downtime", {})
            data.setdefault(
                "handshake",
                {"acknowledgement": "", "capabilities": [], "downtime": {}},
            )
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(data, indent=2))


def _emit_event(step: str, status: str, **details: Any) -> None:
    """Append a structured health event to :data:`STATE_FILE`."""
    data: Dict[str, Any] = {}
    with STATE_FILE_LOCK:
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
            except json.JSONDecodeError:
                data = {}
        events = data.setdefault("events", [])
        event = {"step": step, "status": status, "timestamp": time.time()}
        if details:
            event.update(details)
        events.append(event)
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(data, indent=2))


def _record_probe(name: str, ok: bool) -> None:
    """Persist the result of a component health probe."""
    data: Dict[str, Any] = {}
    with STATE_FILE_LOCK:
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
            except json.JSONDecodeError:
                data = {}
        probes = data.setdefault("probes", {})
        previous = probes.get(name)
        status = "ok" if ok else "fail"
        probes[name] = {
            "status": status,
            "timestamp": time.time(),
        }
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(data, indent=2))
    if not ok or previous is None or previous.get("status") != status:
        _emit_event("probe", status, component=name)


def _snapshot_agent_config() -> None:
    """Persist the current agent configuration for later rollback."""

    if not AGENT_CONFIG_PATH.exists():
        return
    try:
        AGENT_CONFIG_BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        AGENT_CONFIG_BACKUP_PATH.write_bytes(AGENT_CONFIG_PATH.read_bytes())
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.exception("Failed to snapshot agent configuration for rollback")


def rollback_to_safe_defaults() -> None:
    """Restore the most recent agent configuration snapshot."""

    if not AGENT_CONFIG_BACKUP_PATH.exists():
        LOGGER.warning("No agent configuration snapshot found for rollback")
        return
    try:
        AGENT_CONFIG_PATH.write_bytes(AGENT_CONFIG_BACKUP_PATH.read_bytes())
        LOGGER.info("Restored agent configuration from %s", AGENT_CONFIG_BACKUP_PATH)
        ai_invoker.invalidate_agent_config_cache(AGENT_CONFIG_PATH)
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.exception("Failed to restore agent configuration from snapshot")


def _send_email_alert(recipient: str, subject: str, body: str) -> None:
    """Send an email alert using the configured SMTP relay."""

    message = EmailMessage()
    message["From"] = ALERT_EMAIL_SENDER
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(ALERT_EMAIL_SMTP, ALERT_EMAIL_PORT, timeout=10) as client:
        client.send_message(message)


def send_monitoring_alert(
    message: str,
    *,
    severity: str = "warning",
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Forward ``message`` to configured monitoring backends."""

    timestamp = time.time()
    payload: Dict[str, Any] = {
        "message": message,
        "severity": severity,
        "timestamp": timestamp,
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp)),
    }
    if context:
        payload["context"] = context

    if ALERT_WEBHOOK_URL and requests is not None:
        try:
            response = requests.post(ALERT_WEBHOOK_URL, json=payload, timeout=5)
            if response.status_code >= 400:
                LOGGER.error(
                    "Monitoring webhook responded with status %s: %s",
                    response.status_code,
                    response.text,
                )
        except Exception:  # pragma: no cover - network failure
            LOGGER.exception("Failed to publish monitoring alert via webhook")
    elif ALERT_WEBHOOK_URL:
        LOGGER.warning("Requests unavailable; cannot post monitoring alerts")

    if ALERT_EMAIL_RECIPIENT:
        email_body = message
        if context:
            email_body += "\n\n" + json.dumps(context, indent=2, default=str)
        try:
            _send_email_alert(
                ALERT_EMAIL_RECIPIENT,
                f"[RAZAR] {severity.upper()} alert",
                email_body,
            )
        except Exception:  # pragma: no cover - smtp failure
            LOGGER.exception("Failed to dispatch monitoring alert email")

    try:
        MONITORING_ALERTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = MONITORING_ALERTS_DIR / f"razar_{int(timestamp * 1000)}.json"
        file_path.write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
    except Exception:  # pragma: no cover - filesystem failure
        LOGGER.exception("Failed to persist monitoring alert payload")


def _execute_health_probe(component: Dict[str, Any]) -> bool:
    """Run the configured health probe for ``component``."""

    name = str(component.get("name", ""))
    cmd = component.get("health_check")
    if cmd:
        try:
            result = subprocess.run(cmd, check=False)
        except Exception:  # pragma: no cover - subprocess failure
            LOGGER.exception("Health check command errored for %s", name)
            return False
        return result.returncode == 0

    ok = health_checks.run(name)
    if name not in health_checks.CHECKS:
        LOGGER.warning("No health probe defined for %s", name)
    return ok


def _periodic_probe_loop(
    components_ref: Dict[str, Dict[str, Any]],
    processes_ref: Dict[str, subprocess.Popen],
    escalation_tracker: Dict[str, int],
    stop_event: threading.Event,
    lock: threading.Lock,
) -> None:
    """Background worker executing periodic health probes."""

    alerted_components: Dict[str, int] = {}
    while not stop_event.wait(HEALTH_PROBE_INTERVAL):
        with lock:
            components_snapshot = dict(components_ref)
            processes_snapshot = dict(processes_ref)
            escalation_snapshot = dict(escalation_tracker)

        for name, component in components_snapshot.items():
            proc = processes_snapshot.get(name)
            if proc is None or proc.poll() is not None:
                continue
            ok = _execute_health_probe(component)
            _record_probe(name, ok)
            if not ok:
                warning = f"Periodic health probe failed for {name}"
                LOGGER.warning(warning)
                send_monitoring_alert(
                    warning,
                    severity="critical",
                    context={"component": name, "probe": "periodic"},
                )

        if ESCALATION_WARNING_THRESHOLD <= 0:
            continue

        for name, count in escalation_snapshot.items():
            if count < ESCALATION_WARNING_THRESHOLD:
                continue
            last_alert = alerted_components.get(name)
            if last_alert is not None and count <= last_alert:
                continue
            warning = (
                f"Component {name} triggered {count} escalations during the current "
                "boot cycle"
            )
            LOGGER.warning(warning)
            send_monitoring_alert(
                warning,
                severity="warning",
                context={"component": name, "escalations": count},
            )
            alerted_components[name] = count


def build_failure_context(component: str, limit: int = 5) -> Dict[str, Any]:
    """Return recent failure history for ``component``.

    The history is read from the shared invocation log and truncated to the
    most recent ``limit`` entries. The returned structure matches the expected
    AI handover context format so downstream agents can reference prior
    attempts.
    """

    history_entries = load_invocation_history(component, limit)
    if not history_entries:
        return {}

    allowed_keys = {
        "attempt",
        "error",
        "patched",
        "event",
        "agent",
        "agent_original",
        "timestamp",
        "timestamp_iso",
        "status",
    }

    history = [
        {key: entry[key] for key in allowed_keys if key in entry}
        for entry in history_entries
    ]

    return {"history": history}


def _log_long_task(
    component: str,
    attempt: int,
    error: str,
    patched: bool,
    *,
    aborted: bool = False,
) -> None:
    """Append long-task attempt details to :data:`LONG_TASK_LOG_PATH`."""
    entry = {
        "component": component,
        "attempt": attempt,
        "error": error,
        "patched": patched,
        "aborted": aborted,
        "timestamp": time.time(),
    }
    records: List[Dict[str, Any]] = []
    if LONG_TASK_LOG_PATH.exists():
        try:
            records = json.loads(LONG_TASK_LOG_PATH.read_text())
            if not isinstance(records, list):
                records = []
        except json.JSONDecodeError:
            records = []
    records.append(entry)
    LONG_TASK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LONG_TASK_LOG_PATH.write_text(json.dumps(records, indent=2))


def _should_escalate(failure_count: int) -> bool:
    """Return ``True`` when persistent failures warrant escalation."""

    threshold = RSTAR_THRESHOLD
    if threshold <= 0:
        return False
    return failure_count % threshold == 0


def _set_active_agent(agent: str) -> None:
    """Set the active remote agent in :data:`AGENT_CONFIG_PATH`."""
    try:
        data = json.loads(AGENT_CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    data["active"] = agent
    AGENT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    AGENT_CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    ai_invoker.invalidate_agent_config_cache(AGENT_CONFIG_PATH)


def _load_agent_state() -> tuple[Optional[str], list[str], dict[str, str]]:
    """Return the active agent and ordered failover chain from configuration."""

    active_agent, definitions = ai_invoker.load_agent_definitions(AGENT_CONFIG_PATH)
    normalized_active = active_agent.lower() if isinstance(active_agent, str) else None
    sequence = [definition.normalized for definition in definitions]
    lookup = {definition.normalized: definition.name for definition in definitions}
    return normalized_active, sequence, lookup


def _handle_ai_result(
    name: str,
    error: str,
    patched: bool,
    attempt: int,
    failure_tracker: Dict[str, int],
    escalation_tracker: Optional[Dict[str, int]] = None,
    escalation_lock: Optional[threading.Lock] = None,
) -> None:
    """Update failure counter and escalate persistent issues."""
    if patched:
        failure_tracker[name] = 0
        return
    count = failure_tracker.get(name, 0) + 1
    failure_tracker[name] = count
    if not _should_escalate(count):
        return
    try:
        active_agent, sequence, lookup = _load_agent_state()
    except ai_invoker.AgentCredentialError as exc:
        LOGGER.warning("Skipping remote escalation for %s: %s", name, exc)
        return
    if active_agent is not None:
        active_agent = active_agent.lower()
    sequence = [agent.lower() for agent in sequence]
    if not sequence:
        return

    if active_agent in sequence:
        idx = sequence.index(active_agent)
        next_agent = sequence[idx + 1] if idx + 1 < len(sequence) else None
    else:
        next_agent = sequence[0]

    if next_agent:
        normalized_next = next_agent.lower()
        original_next = lookup.get(normalized_next, normalized_next)
        if escalation_tracker is not None:
            if escalation_lock is not None:
                with escalation_lock:
                    escalation_tracker[name] = escalation_tracker.get(name, 0) + 1
            else:
                escalation_tracker[name] = escalation_tracker.get(name, 0) + 1
        _set_active_agent(original_next)
        append_invocation_event(
            {
                "component": name,
                "attempt": attempt,
                "error": error,
                "patched": patched,
                "event": "escalation",
                "agent": normalized_next,
                "agent_original": original_next,
            }
        )


def _retry_with_ai(
    name: str,
    component: Dict[str, Any],
    error_msg: str,
    max_attempts: int,
    failure_tracker: Dict[str, int],
    escalation_tracker: Optional[Dict[str, int]] = None,
    escalation_lock: Optional[threading.Lock] = None,
) -> tuple[Optional[subprocess.Popen], int, str]:
    """Invoke AI handover until success or ``max_attempts`` is reached.

    ``failure_tracker`` records consecutive :mod:`ai_invoker` failures per
    component.  Returns a tuple of ``(process, attempts, error)`` where
    ``process`` is the relaunched component on success, ``attempts`` is the
    number of AI retries performed, and ``error`` is the last error message
    encountered.
    """
    attempts_used = 0
    last_patched = False
    last_agent: Optional[str] = None
    final_proc: Optional[subprocess.Popen] = None
    final_error = error_msg
    success = False
    retry_start = time.perf_counter()

    try:
        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            attempt_start = time.perf_counter()
            handover_duration = 0.0
            agent_label = "unknown"
            attempt_outcome = "handover_failed"
            use_opencode = False
            patched = False

            try:
                active_agent, agent_chain, lookup = _load_agent_state()
            except Exception:  # pragma: no cover - defensive guard
                active_agent, agent_chain, lookup = None, [], {}

            if isinstance(active_agent, str):
                active_agent = active_agent.lower()

            use_opencode = active_agent not in agent_chain
            context = build_failure_context(name)
            hand_start = time.perf_counter()
            patched = ai_invoker.handover(
                name,
                error_msg,
                context=context,
                use_opencode=use_opencode,
            )
            handover_duration = time.perf_counter() - hand_start
            agent_label = (
                "opencode" if use_opencode else (active_agent or "remote_agent")
            )
            last_agent = agent_label
            last_patched = bool(patched)

            agent_original = None
            if isinstance(active_agent, str):
                agent_original = lookup.get(active_agent, active_agent)

            log_invocation(
                name,
                attempt,
                error_msg,
                patched,
                agent=active_agent,
                agent_original=agent_original,
            )
            _handle_ai_result(
                name,
                error_msg,
                patched,
                attempt,
                failure_tracker,
                escalation_tracker,
                escalation_lock,
            )
            final_error = error_msg

            try:
                if not patched:
                    attempt_outcome = "no_patch"
                    continue

                attempt_outcome = "patch_applied"
                LOGGER.info(
                    "Retrying %s after AI patch (remote attempt %s)", name, attempt
                )
                proc = launch_component(component)
                # Re-run the health check after patch application to confirm recovery
                if not _execute_health_probe(component):
                    _record_probe(name, False)
                    proc.terminate()
                    proc.wait()
                    LOGGER.error("Post-patch health check failed for %s", name)
                    attempt_outcome = "health_check_failed"
                    continue
                final_proc = proc
                final_error = error_msg
                success = True
                attempt_outcome = "relaunch_success"
                break
            except Exception as exc:  # pragma: no cover - complex patch failure
                error_msg = str(exc)
                final_error = error_msg
                LOGGER.error("Remote attempt %s failed for %s: %s", attempt, name, exc)
                attempt_outcome = "relaunch_error"
            finally:
                attempt_duration = time.perf_counter() - attempt_start
                LOGGER.info(
                    "AI retry attempt completed",
                    extra={
                        "component": name,
                        "attempt": attempt,
                        "agent": agent_label,
                        "duration": attempt_duration,
                        "handover_duration": handover_duration,
                        "patched": last_patched,
                        "outcome": attempt_outcome,
                        "use_opencode": use_opencode,
                    },
                )
    finally:
        total_duration = time.perf_counter() - retry_start
        metrics.observe_retry_duration(name, total_duration)
        LOGGER.info(
            "AI retry loop finished",
            extra={
                "component": name,
                "attempts": attempts_used,
                "duration": total_duration,
                "patched": last_patched,
                "agent": last_agent,
                "success": success,
            },
        )

    if not success:
        return None, attempts_used or max_attempts, final_error
    return final_proc, attempts_used, final_error


def _rotate_mission_briefs(archive_dir: Path, limit: int = MAX_MISSION_BRIEFS) -> None:
    """Remove oldest mission briefs beyond ``limit`` pairs."""
    briefs = sorted(
        [p for p in archive_dir.glob("*.json") if "_response" not in p.name],
        key=lambda p: p.stat().st_mtime,
    )
    excess = len(briefs) - limit
    for old in briefs[:excess]:
        response_file = old.with_name(f"{old.stem}_response.json")
        if old.exists():
            old.unlink()
        if response_file.exists():
            response_file.unlink()


def _ensure_glm4v(capabilities: List[str]) -> None:
    """Ensure the GLM-4.1V model is available, launching it if required."""
    normalized = {c.replace("-", "").upper() for c in capabilities}
    present = any(c.startswith("GLM4V") for c in normalized)

    data: Dict[str, Any] = {}
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    data["glm4v_present"] = present

    if present:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    launcher = Path(__file__).resolve().parents[1] / "crown_model_launcher.sh"
    LOGGER.info("Launching GLM-4.1V via %s", launcher)
    proc = subprocess.Popen(["bash", str(launcher)])
    returncode = 0
    if hasattr(proc, "wait"):
        proc.wait()
        returncode = getattr(proc, "returncode", 0)
    status = "success" if returncode == 0 else "failure"
    mission_logger.log_event("model_launch", "GLM-4.1V", status, "")
    launches = data.get("launched_models", [])
    if "GLM-4.1V" not in launches:
        launches.append("GLM-4.1V")
    data["launched_models"] = launches
    data["last_model_launch"] = {
        "model": "GLM-4.1V",
        "status": status,
        "returncode": returncode,
        "output": "",
    }

    archive_dir = LOGS_DIR / "mission_briefs"
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    brief_path = archive_dir / f"{timestamp}_glm4v_launch.json"
    response_path = archive_dir / f"{timestamp}_glm4v_launch_response.json"
    brief_path.write_text(
        json.dumps({"event": "model_launch", "model": "GLM-4.1V"}),
        encoding="utf-8",
    )
    response_path.write_text(
        json.dumps({"status": status, "returncode": returncode}),
        encoding="utf-8",
    )
    _rotate_mission_briefs(archive_dir)

    timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    events = data.get("events", [])
    events.append(
        {"event": "model_launch", "model": "GLM-4.1V", "timestamp": timestamp_iso}
    )
    data["events"] = events

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _perform_handshake(components: List[Dict[str, Any]]) -> CrownResponse:
    """Exchange mission brief with CROWN and return the response."""
    brief = {
        "priority_map": {
            str(c.get("name", "")): idx for idx, c in enumerate(components)
        },
        "current_status": {},
        "open_issues": [],
    }
    brief_path = LOGS_DIR / "mission_brief.json"
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(json.dumps(brief, indent=2))

    archive_dir = LOGS_DIR / "mission_briefs"
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    brief_archive = archive_dir / f"{timestamp}.json"
    brief_archive.write_text(json.dumps(brief, indent=2))
    response_path = archive_dir / f"{timestamp}_response.json"

    _emit_event("handshake", "start")
    try:
        response = asyncio.run(crown_handshake.perform(str(brief_path)))
        details = json.dumps(
            {"capabilities": response.capabilities, "downtime": response.downtime}
        )
        status = "success"
        _emit_event("handshake", "success", capabilities=response.capabilities)
    except Exception as exc:  # pragma: no cover - handshake must succeed
        LOGGER.exception("CROWN handshake failed")
        mission_logger.log_event("handshake", "crown", "failure", str(exc))
        _persist_handshake(None)
        _emit_event("handshake", "fail", error=str(exc))
        if init_kimicho is not None:
            LOGGER.info(
                "Handshake failed; invoking Kimicho to initialize K2 Coder "
                "LLM from HuggingFacc"
            )
            try:
                init_kimicho("https://huggingfacc.com/k2coder")
                mission_logger.log_event("handshake", "kimicho", "init", "huggingfacc")
                _emit_event("handshake", "fallback", engine="kimicho")
            except Exception as kimicho_exc:  # pragma: no cover - kimicho optional
                LOGGER.exception("Kimicho initialization failed")
                mission_logger.log_event(
                    "handshake", "kimicho", "failure", str(kimicho_exc)
                )
        else:
            LOGGER.warning(
                "Kimicho bindings unavailable; cannot initialize K2 fallback"
            )
        raise RuntimeError("CROWN handshake failed") from exc

    mission_logger.log_event("handshake", "crown", status, details)
    _persist_handshake(response)
    _ensure_glm4v(response.capabilities)
    response_path.write_text(json.dumps(asdict(response), indent=2))
    _rotate_mission_briefs(archive_dir)

    return response


def load_config(path: Path) -> List[Dict[str, Any]]:
    """Return ordered component definitions from ``path``.

    ``path`` points to a JSON file with a ``components`` list.
    """
    data = json.loads(path.read_text())
    components = data.get("components", [])
    for comp in components:
        name = comp.get("name", "")
        has_probe = comp.get("health_check") or name in health_checks.CHECKS
        if not has_probe:
            raise ValueError(f"Component {name} lacks a health probe")
    return components


def launch_component(component: Dict[str, Any]) -> subprocess.Popen:
    """Launch ``component`` and run its health check.

    ``component`` may specify a ``health_check`` command. If absent, a named
    probe from :mod:`health_checks` is used. When no probe exists, a warning is
    logged and the component is assumed healthy.
    """
    name = str(component.get("name"))
    LOGGER.info("Launching %s", name)
    _emit_event("launch", "start", component=name)
    proc = subprocess.Popen(component["command"])

    ok = _execute_health_probe(component)
    _record_probe(name, ok)
    if not ok:
        LOGGER.error("Health check failed for %s", name)
        proc.terminate()
        proc.wait()
        _emit_event("launch", "fail", component=name)
        raise RuntimeError(f"Health check failed for {name}")
    LOGGER.info("%s started successfully", name)
    _emit_event("launch", "success", component=name)
    return proc


def main() -> None:
    """CLI entry point for manual runs."""
    parser = argparse.ArgumentParser(description="Launch components from configuration")
    default_cfg = Path(__file__).with_name("boot_config.json")
    parser.add_argument(
        "--config", type=Path, default=default_cfg, help="Path to configuration file"
    )
    parser.add_argument(
        "--retries", type=int, default=3, help="Retries for failed launches"
    )
    parser.add_argument(
        "--failure-limit",
        type=int,
        default=3,
        help="Quarantine component after N cumulative failures",
    )
    parser.add_argument(
        "--remote-attempts",
        type=int,
        default=3,
        help="AI handover attempts after local retries fail",
    )
    parser.add_argument(
        "--long-task",
        action="store_true",
        help="Repeatedly invoke AI handover until success or operator aborts",
    )
    args = parser.parse_args()

    log_file = Path(__file__).with_name("boot_orchestrator.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    metrics.init_metrics()

    load_rust_components()

    components = load_config(args.config)
    _snapshot_agent_config()
    _emit_event("boot_sequence", "start")
    _perform_handshake(components)
    launch_required_agents()
    processes: Dict[str, subprocess.Popen] = {}
    active_components: Dict[str, Dict[str, Any]] = {}
    escalation_counts: Dict[str, int] = {}
    registry_lock = threading.Lock()
    stop_event = threading.Event()
    probe_thread: Optional[threading.Thread] = None
    if HEALTH_PROBE_INTERVAL > 0:
        probe_thread = threading.Thread(
            target=_periodic_probe_loop,
            args=(
                active_components,
                processes,
                escalation_counts,
                stop_event,
                registry_lock,
            ),
            name="razar-health-probes",
            daemon=True,
        )
        probe_thread.start()

    def register_process(
        component_name: str, component_def: Dict[str, Any], proc: subprocess.Popen
    ) -> None:
        with registry_lock:
            processes[component_name] = proc
            active_components[component_name] = component_def

    history = load_history()
    failure_counts: Dict[str, int] = history.get("component_failures", {})
    ai_failure_counts: Dict[str, int] = {}
    run_start = time.time()
    run_metrics: Dict[str, Any] = {"timestamp": run_start, "components": []}

    try:
        for comp in components:
            name = str(comp.get("name", ""))
            if is_quarantined(name):
                LOGGER.info("Skipping quarantined component %s", name)
                continue
            if failure_counts.get(name, 0) >= args.failure_limit:
                LOGGER.warning(
                    "Component %s exceeded failure limit; quarantining", name
                )
                quarantine_component(comp, "Exceeded failure limit")
                continue

            attempts = 0
            success = False
            for attempt in range(1, args.retries + 2):
                attempts = attempt
                try:
                    proc = launch_component(comp)
                    register_process(name, comp, proc)
                    success = True
                    break
                except Exception as exc:
                    LOGGER.error("Attempt %s failed for %s: %s", attempt, name, exc)
                    if attempt > args.retries:
                        error_msg = str(exc)
                        if args.long_task:
                            r_attempt = 0
                            while True:
                                r_attempt += 1
                                try:
                                    patched = ai_invoker.handover(
                                        name,
                                        error_msg,
                                        context=build_failure_context(name),
                                        use_opencode=True,
                                    )
                                    log_invocation(name, r_attempt, error_msg, patched)
                                    _handle_ai_result(
                                        name,
                                        error_msg,
                                        patched,
                                        r_attempt,
                                        ai_failure_counts,
                                        escalation_counts,
                                        registry_lock,
                                    )
                                    _log_long_task(name, r_attempt, error_msg, patched)
                                except KeyboardInterrupt:
                                    _log_long_task(
                                        name,
                                        r_attempt,
                                        error_msg,
                                        False,
                                        aborted=True,
                                    )
                                    LOGGER.info(
                                        "Operator aborted long task for %s", name
                                    )
                                    raise
                                if not patched:
                                    continue
                                LOGGER.info(
                                    "Retrying %s after AI patch (long task attempt %s)",
                                    name,
                                    r_attempt,
                                )
                                try:
                                    attempts += 1
                                    proc = launch_component(comp)
                                    # run a second health check to verify recovery
                                    if not _execute_health_probe(comp):
                                        _record_probe(name, False)
                                        proc.terminate()
                                        proc.wait()
                                        LOGGER.error(
                                            "Post-patch health check failed for %s",
                                            name,
                                        )
                                        continue
                                    register_process(name, comp, proc)
                                    success = True
                                    break
                                except Exception as exc2:
                                    attempts += 1
                                    error_msg = str(exc2)
                                    LOGGER.error(
                                        "Long task attempt %s failed for %s: %s",
                                        r_attempt,
                                        name,
                                        exc2,
                                    )
                            if success:
                                break
                        else:
                            patched_proc, ai_attempts, error_msg = _retry_with_ai(
                                name,
                                comp,
                                error_msg,
                                args.remote_attempts,
                                ai_failure_counts,
                                escalation_counts,
                                registry_lock,
                            )
                            attempts += ai_attempts
                            if patched_proc is not None:
                                register_process(name, comp, patched_proc)
                                success = True
                                break
                        failure_counts[name] = failure_counts.get(name, 0) + 1
                        quarantine_component(comp, error_msg)
                        run_metrics["components"].append(
                            {"name": name, "attempts": attempts, "success": False}
                        )
                        raise
                    backoff = min(2 ** (attempt - 1), 60)
                    time.sleep(backoff)

            if success:
                run_metrics["components"].append(
                    {"name": name, "attempts": attempts, "success": True}
                )

        LOGGER.info("All components launched")
        doc_sync.sync_docs()
        _emit_event("doc_sync", "success")
        for proc in list(processes.values()):
            proc.wait()
    except Exception as exc:  # pragma: no cover - logs on failure
        LOGGER.exception("Boot sequence halted")
        for proc in list(processes.values()):
            proc.terminate()
            proc.wait()
        rollback_to_safe_defaults()
        send_monitoring_alert(
            "Boot sequence halted; configuration rolled back to safe defaults",
            severity="critical",
            context={"error": str(exc)},
        )
        raise SystemExit(1)
    finally:
        stop_event.set()
        if probe_thread is not None:
            probe_thread.join(timeout=5)
        finalize_metrics(run_metrics, history, failure_counts, run_start)
        _emit_event(
            "boot_sequence",
            "complete",
            success_rate=run_metrics.get("success_rate", 0.0),
        )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
