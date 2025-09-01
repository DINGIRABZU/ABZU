"""Simple boot orchestrator reading a JSON component configuration.

The orchestrator launches components from basic to complex as defined in the
configuration file. A health check hook runs after each launch and any failure
halts the boot sequence. Failed components are quarantined and skipped on
subsequent runs.
"""

from __future__ import annotations

__version__ = "0.2.4"

import argparse
import asyncio
import json
import logging
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import ai_invoker, crown_handshake, doc_sync, health_checks, mission_logger
from .crown_handshake import CrownResponse
from .quarantine_manager import is_quarantined, quarantine_component
from agents.nazarick.service_launcher import launch_required_agents

LOGGER = logging.getLogger("razar.boot_orchestrator")

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
HISTORY_FILE = LOGS_DIR / "razar_boot_history.json"
STATE_FILE = LOGS_DIR / "razar_state.json"
# keep a limited number of mission brief archives for auditability
MAX_MISSION_BRIEFS = 20


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
    else:
        data.setdefault("capabilities", [])
        data.setdefault("downtime", {})
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2))


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
    subprocess.run(["bash", str(launcher)], check=False)
    mission_logger.log_event("model_launch", "GLM-4.1V", "triggered")
    launches = data.get("launched_models", [])
    if "GLM-4.1V" not in launches:
        launches.append("GLM-4.1V")
    data["launched_models"] = launches

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
        json.dumps({"status": "triggered"}),
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

    try:
        response = asyncio.run(crown_handshake.perform(str(brief_path)))
        details = json.dumps(
            {"capabilities": response.capabilities, "downtime": response.downtime}
        )
        status = "success"
    except Exception as exc:  # pragma: no cover - handshake must succeed
        LOGGER.exception("CROWN handshake failed")
        mission_logger.log_event("handshake", "crown", "failure", str(exc))
        _persist_handshake(None)
        raise RuntimeError("CROWN handshake failed") from exc

    mission_logger.log_event("handshake", "crown", status, details)
    _persist_handshake(response)
    response_path.write_text(json.dumps(asdict(response), indent=2))
    _rotate_mission_briefs(archive_dir)

    return response


def load_config(path: Path) -> List[Dict[str, Any]]:
    """Return ordered component definitions from ``path``.

    ``path`` points to a JSON file with a ``components`` list.
    """
    data = json.loads(path.read_text())
    return data.get("components", [])


def launch_component(component: Dict[str, Any]) -> subprocess.Popen:
    """Launch ``component`` and run its health check."""
    name = component.get("name")
    LOGGER.info("Launching %s", name)
    proc = subprocess.Popen(component["command"])
    if not health_checks.run(name):
        LOGGER.error("Health check failed for %s", name)
        proc.terminate()
        proc.wait()
        raise RuntimeError(f"Health check failed for {name}")
    LOGGER.info("%s started successfully", name)
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
    args = parser.parse_args()

    log_file = Path(__file__).with_name("boot_orchestrator.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    components = load_config(args.config)
    response = _perform_handshake(components)
    _ensure_glm4v(response.capabilities)
    launch_required_agents()
    processes: List[subprocess.Popen] = []

    history = load_history()
    failure_counts: Dict[str, int] = history.get("component_failures", {})
    run_start = time.time()
    run_metrics: Dict[str, Any] = {"timestamp": run_start, "components": []}

    try:
        for comp in components:
            name = comp.get("name", "")
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
                        # escalate to remote agent for potential repair
                        patched = ai_invoker.handover(name, str(exc))
                        if patched:
                            LOGGER.info("Retrying %s after AI patch", name)
                            try:
                                proc = launch_component(comp)
                                processes.append(proc)
                                success = True
                                attempts += 1
                                break
                            except Exception as exc2:
                                LOGGER.error(
                                    "Retry after AI patch failed for %s: %s",
                                    name,
                                    exc2,
                                )
                        failure_counts[name] = failure_counts.get(name, 0) + 1
                        quarantine_component(comp, str(exc))
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


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
