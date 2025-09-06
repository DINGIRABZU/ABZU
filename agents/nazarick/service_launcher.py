"""Start core Nazarick agents after the Crown handshake."""

from __future__ import annotations

import asyncio
import json
import logging
import shlex
import subprocess
import threading
import time
from pathlib import Path

from .chakra_observer import NazarickChakraObserver
from agents.event_bus import emit_event

__version__ = "0.1.2"

LOGGER = logging.getLogger(__name__)

REGISTRY_FILE = Path(__file__).with_name("agent_registry.json")
LOG_FILE = Path("logs") / "nazarick_startup.json"


def launch_required_agents(registry_path: Path | None = None) -> list[dict[str, str]]:
    """Launch required agents from a registry and log activation events.

    Parameters
    ----------
    registry_path:
        Optional override path to the agent registry JSON.

    Returns
    -------
    list[dict[str, str]]
        Event dictionaries describing each launch attempt. Each event contains
        ``agent``, ``command``, ``timestamp``, ``channel`` and ``status`` fields.
        On failure an additional ``error`` field is included.
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        existing = json.loads(LOG_FILE.read_text()) if LOG_FILE.exists() else []
    except json.JSONDecodeError:  # pragma: no cover - corrupt file
        existing = []

    registry_file = Path(registry_path) if registry_path else REGISTRY_FILE
    try:
        registry = json.loads(registry_file.read_text()) or {}
        entries = registry.get("agents", [])
    except FileNotFoundError:  # pragma: no cover - missing registry
        LOGGER.error("Agent registry not found: %s", registry_file)
        entries = []

    events: list[dict[str, str]] = []
    for entry in entries:
        name = entry.get("id", "")
        cmd_str = entry.get("launch")
        channel = entry.get("channel", "")
        capabilities = entry.get("capabilities", [])
        triggers = entry.get("triggers", [])
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        event: dict[str, str] = {
            "agent": name,
            "command": cmd_str or "",
            "channel": channel,
            "timestamp": timestamp,
        }
        if not cmd_str:
            event["status"] = "skipped"
            events.append(event)
            emit_event(
                name, "register", {"capabilities": capabilities, "triggers": triggers}
            )
            continue

        cmd = shlex.split(cmd_str)
        try:
            subprocess.Popen(cmd)
            event["status"] = "launched"
            LOGGER.info("Launched %s", name)
            emit_event(
                name, "register", {"capabilities": capabilities, "triggers": triggers}
            )

            def _relaunch() -> bool:
                try:
                    subprocess.Popen(cmd)
                    LOGGER.info("Relaunched %s", name)
                    return True
                except Exception:
                    LOGGER.exception("Failed to relaunch %s", name)
                    return False

            observer = NazarickChakraObserver(name, _relaunch)
            threading.Thread(
                target=lambda: asyncio.run(observer.run()), daemon=True
            ).start()
        except Exception as exc:  # pragma: no cover - best effort logging
            event["status"] = "error"
            event["error"] = str(exc)
            LOGGER.exception("Failed to launch %s", name)
            emit_event(
                name, "register", {"capabilities": capabilities, "triggers": triggers}
            )
        events.append(event)

    LOG_FILE.write_text(json.dumps(existing + events, indent=2))
    return events


__all__ = ["launch_required_agents"]
