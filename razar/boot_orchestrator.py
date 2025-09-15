"""Simple boot orchestrator reading a JSON component configuration.

The orchestrator launches components from basic to complex as defined in the
configuration file. A health check hook runs after each launch and any failure
halts the boot sequence. Failed components are quarantined and skipped on
subsequent runs.
"""

from __future__ import annotations

__version__ = "0.2.11"

import argparse
import asyncio
import json
import logging
import os
import subprocess
import time
from dataclasses import asdict
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

from . import ai_invoker, crown_handshake, doc_sync, health_checks, mission_logger
from .bootstrap_utils import (
    HISTORY_FILE,
    LOGS_DIR,
    MAX_MISSION_BRIEFS,
    STATE_FILE,
)
from .crown_handshake import CrownResponse
from .quarantine_manager import is_quarantined, quarantine_component
from agents.nazarick.service_launcher import launch_required_agents

LOGGER = logging.getLogger("razar.boot_orchestrator")


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


# Path for recording AI handover attempts
INVOCATION_LOG_PATH = LOGS_DIR / "razar_ai_invocations.json"
LONG_TASK_LOG_PATH = LOGS_DIR / "razar_long_task.json"
AGENT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "razar_ai_agents.json"
)
RSTAR_THRESHOLD = int(os.getenv("RAZAR_RSTAR_THRESHOLD", 9))


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
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            data = {}
    probes = data.setdefault("probes", {})
    probes[name] = {
        "status": "ok" if ok else "fail",
        "timestamp": time.time(),
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2))
    _emit_event("probe", "ok" if ok else "fail", component=name)


def _log_ai_invocation(
    component: str,
    attempt: int,
    error: str,
    patched: bool,
    *,
    event: str = "attempt",
    agent: str | None = None,
) -> None:
    """Append AI handover attempt details to :data:`INVOCATION_LOG_PATH`."""
    entry = {
        "component": component,
        "attempt": attempt,
        "error": error,
        "patched": patched,
        "event": event,
        "timestamp": time.time(),
    }
    if agent is not None:
        entry["agent"] = agent
    records: List[Dict[str, Any]] = []
    if INVOCATION_LOG_PATH.exists():
        try:
            records = json.loads(INVOCATION_LOG_PATH.read_text())
            if not isinstance(records, list):
                records = []
        except json.JSONDecodeError:
            records = []
    records.append(entry)
    INVOCATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVOCATION_LOG_PATH.write_text(json.dumps(records, indent=2))


def build_failure_context(component: str, limit: int = 5) -> Dict[str, Any]:
    """Return recent failure history for ``component``.

    The history is read from :data:`INVOCATION_LOG_PATH` and truncated to the
    most recent ``limit`` entries. The returned structure matches the expected
    AI handover context format so downstream agents can reference prior
    attempts.
    """
    if not INVOCATION_LOG_PATH.exists():
        return {}
    try:
        records = json.loads(INVOCATION_LOG_PATH.read_text())
        if not isinstance(records, list):
            return {}
    except json.JSONDecodeError:
        return {}

    history: List[Dict[str, Any]] = []
    for entry in records:
        if entry.get("component") != component:
            continue
        record = {
            key: entry.get(key)
            for key in ("attempt", "error", "patched", "agent", "event", "timestamp")
        }
        agent = record.get("agent")
        if isinstance(agent, str):
            record["agent"] = agent.lower()
        history.append(record)
    history.sort(key=lambda e: e.get("timestamp", 0))
    if not history:
        return {}
    return {"history": history[-limit:]}


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


def _load_agent_state() -> tuple[Optional[str], list[str], dict[str, str]]:
    """Return the active agent and ordered failover chain from configuration."""

    active_agent: Optional[str] = None
    sequence: list[str] = []
    lookup: dict[str, str] = {}
    try:
        data = json.loads(AGENT_CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    raw_active = data.get("active") if isinstance(data, dict) else None
    if isinstance(raw_active, str):
        active_agent = raw_active.lower()

    agents = data.get("agents") if isinstance(data, dict) else None
    if isinstance(agents, list):
        for entry in agents:
            if isinstance(entry, dict):
                name = entry.get("name")
            elif isinstance(entry, str):
                name = entry
            else:
                continue
            if not isinstance(name, str):
                continue
            normalized = name.lower()
            sequence.append(normalized)
            lookup.setdefault(normalized, name)

    return active_agent, sequence, lookup


def _handle_ai_result(
    name: str,
    error: str,
    patched: bool,
    attempt: int,
    failure_tracker: Dict[str, int],
) -> None:
    """Update failure counter and escalate persistent issues."""
    if patched:
        failure_tracker[name] = 0
        return
    count = failure_tracker.get(name, 0) + 1
    failure_tracker[name] = count
    if not _should_escalate(count):
        return
    active_agent, sequence, lookup = _load_agent_state()
    if not sequence:
        return

    if active_agent in sequence:
        idx = sequence.index(active_agent)
        next_agent = sequence[idx + 1] if idx + 1 < len(sequence) else None
    else:
        next_agent = sequence[0]

    if next_agent:
        _set_active_agent(lookup.get(next_agent, next_agent))
        _log_ai_invocation(
            name, attempt, error, patched, event="escalation", agent=next_agent
        )


def _retry_with_ai(
    name: str,
    component: Dict[str, Any],
    error_msg: str,
    max_attempts: int,
    failure_tracker: Dict[str, int],
) -> tuple[Optional[subprocess.Popen], int, str]:
    """Invoke AI handover until success or ``max_attempts`` is reached.

    ``failure_tracker`` records consecutive :mod:`ai_invoker` failures per
    component.  Returns a tuple of ``(process, attempts, error)`` where
    ``process`` is the relaunched component on success, ``attempts`` is the
    number of AI retries performed, and ``error`` is the last error message
    encountered.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            active_agent, agent_chain, _ = _load_agent_state()
        except Exception:  # pragma: no cover - defensive guard
            active_agent, agent_chain = None, []
        use_opencode = active_agent not in agent_chain
        context = build_failure_context(name)
        patched = ai_invoker.handover(
            name,
            error_msg,
            context=context,
            use_opencode=use_opencode,
        )
        _log_ai_invocation(name, attempt, error_msg, patched, agent=active_agent)
        _handle_ai_result(name, error_msg, patched, attempt, failure_tracker)
        if not patched:
            continue
        LOGGER.info("Retrying %s after AI patch (remote attempt %s)", name, attempt)
        try:
            proc = launch_component(component)
            # Re-run the health check after patch application to confirm recovery
            if not health_checks.run(name):
                proc.terminate()
                proc.wait()
                LOGGER.error("Post-patch health check failed for %s", name)
                continue
            return proc, attempt, error_msg
        except Exception as exc:  # pragma: no cover - complex patch failure
            error_msg = str(exc)
            LOGGER.error("Remote attempt %s failed for %s: %s", attempt, name, exc)
    return None, max_attempts, error_msg


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

    cmd = component.get("health_check")
    if cmd:
        result = subprocess.run(cmd)
        ok = result.returncode == 0
    else:
        ok = health_checks.run(name)
        if name not in health_checks.CHECKS:
            LOGGER.warning("No health probe defined for %s", name)
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

    load_rust_components()

    components = load_config(args.config)
    _emit_event("boot_sequence", "start")
    _perform_handshake(components)
    launch_required_agents()
    processes: List[subprocess.Popen] = []

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
                    processes.append(proc)
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
                                        name, error_msg, use_opencode=True
                                    )
                                    _log_ai_invocation(
                                        name, r_attempt, error_msg, patched
                                    )
                                    _handle_ai_result(
                                        name,
                                        error_msg,
                                        patched,
                                        r_attempt,
                                        ai_failure_counts,
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
                                    if not health_checks.run(name):
                                        proc.terminate()
                                        proc.wait()
                                        LOGGER.error(
                                            "Post-patch health check failed for %s",
                                            name,
                                        )
                                        continue
                                    processes.append(proc)
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
                            )
                            attempts += ai_attempts
                            if patched_proc is not None:
                                processes.append(patched_proc)
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
        for proc in processes:
            proc.wait()
    except Exception:  # pragma: no cover - logs on failure
        LOGGER.exception("Boot sequence halted")
        for proc in processes:
            proc.terminate()
            proc.wait()
        raise SystemExit(1)
    finally:
        finalize_metrics(run_metrics, history, failure_counts, run_start)
        _emit_event(
            "boot_sequence",
            "complete",
            success_rate=run_metrics.get("success_rate", 0.0),
        )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
