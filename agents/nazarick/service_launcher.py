"""Start core Nazarick agents after the Crown handshake."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path

__version__ = "0.1.1"

LOGGER = logging.getLogger(__name__)

# Mapping of agent identifiers to the command launching them.
REQUIRED_AGENTS: dict[str, list[str]] = {
    "orchestration_master": ["python", "orchestration_master.py"],
    "prompt_orchestrator": ["python", "crown_prompt_orchestrator.py"],
    "qnl_engine": ["python", "SPIRAL_OS/qnl_engine.py"],
    "memory_scribe": ["python", "memory_scribe.py"],
}

LOG_FILE = Path("logs") / "nazarick_startup.json"


def launch_required_agents() -> list[dict[str, str]]:
    """Launch required agents and log activation events.

    Returns a list of event dictionaries describing each launch attempt.
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        existing = json.loads(LOG_FILE.read_text()) if LOG_FILE.exists() else []
    except json.JSONDecodeError:  # pragma: no cover - corrupt file
        existing = []

    events: list[dict[str, str]] = []
    for name, cmd in REQUIRED_AGENTS.items():
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        event = {"agent": name, "command": " ".join(cmd), "timestamp": timestamp}
        try:
            subprocess.Popen(cmd)
            event["status"] = "launched"
            LOGGER.info("Launched %s", name)
        except Exception as exc:  # pragma: no cover - best effort logging
            event["status"] = f"error: {exc}"
            LOGGER.exception("Failed to launch %s", name)
        events.append(event)

    LOG_FILE.write_text(json.dumps(existing + events, indent=2))
    return events


__all__ = ["launch_required_agents"]
