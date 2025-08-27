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
from pathlib import Path
from typing import Any, Dict, List

from .quarantine_manager import is_quarantined, quarantine_component

LOGGER = logging.getLogger("razar.boot_orchestrator")


def load_config(path: Path) -> List[Dict[str, Any]]:
    """Return ordered component definitions from ``path``.

    ``path`` points to a JSON file with a ``components`` list.
    """

    data = json.loads(path.read_text())
    return data.get("components", [])


def run_health_check(command: List[str] | None, timeout: int = 10) -> bool:
    """Run ``command`` and return ``True`` if it exits successfully."""

    if not command:
        return True
    try:
        result = subprocess.run(
            command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
    except (subprocess.TimeoutExpired, OSError) as exc:  # pragma: no cover - defensive
        LOGGER.error("Health check command failed: %s", exc)
        return False
    return result.returncode == 0


def launch_component(component: Dict[str, Any]) -> subprocess.Popen:
    """Launch ``component`` and run its health check."""

    LOGGER.info("Launching %s", component.get("name"))
    proc = subprocess.Popen(component["command"])
    if not run_health_check(component.get("health_check")):
        LOGGER.error("Health check failed for %s", component.get("name"))
        proc.terminate()
        proc.wait()
        raise RuntimeError(f"Health check failed for {component.get('name')}")
    LOGGER.info("%s started successfully", component.get("name"))
    return proc


def main() -> None:
    """CLI entry point for manual runs."""

    parser = argparse.ArgumentParser(description="Launch components from configuration")
    default_cfg = Path(__file__).with_name("boot_config.json")
    parser.add_argument("--config", type=Path, default=default_cfg, help="Path to configuration file")
    args = parser.parse_args()

    log_file = Path(__file__).with_name("boot_orchestrator.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    components = load_config(args.config)
    processes: List[subprocess.Popen] = []
    try:
        for comp in components:
            name = comp.get("name", "")
            if is_quarantined(name):
                LOGGER.info("Skipping quarantined component %s", name)
                continue
            try:
                proc = launch_component(comp)
                processes.append(proc)
            except Exception as exc:
                quarantine_component(comp, str(exc))
                raise
        LOGGER.info("All components launched")
        for proc in processes:
            proc.wait()
    except Exception:  # pragma: no cover - logs on failure
        LOGGER.exception("Boot sequence halted")
        for proc in processes:
            proc.terminate()
            proc.wait()
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
