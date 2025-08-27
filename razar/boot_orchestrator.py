from __future__ import annotations

"""Simple boot orchestrator reading a JSON component configuration.

The orchestrator launches components from basic to complex as defined in the
configuration file. A health check hook runs after each launch and any failure
halts the boot sequence. Failed components are quarantined and skipped on
subsequent runs.
"""

import argparse
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

from . import doc_sync, health_checks
from .quarantine_manager import is_quarantined, quarantine_component

LOGGER = logging.getLogger("razar.boot_orchestrator")

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
HISTORY_FILE = LOGS_DIR / "razar_boot_history.json"


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
                LOGGER.warning("Component %s exceeded failure limit; quarantining", name)
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
