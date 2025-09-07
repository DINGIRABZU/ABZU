"""Shared helpers for chakra healing agents."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
from typing import Any, Iterable

import requests
from agents.event_bus import emit_event, subscribe
from citadel.event_producer import Event

CHAKRACON_URL = "http://localhost:8080"
LOG_PATH = Path("logs") / "chakra_healing.log"
QUARANTINE_LOG = Path("docs") / "quarantine_log.md"


def heal(chakra: str, threshold: float, script_path: Path) -> bool:
    """Poll Chakracon for ``chakra`` and run ``script_path`` if above ``threshold``.

    Returns ``True`` when the healing script was invoked.
    """

    resp = requests.get(f"{CHAKRACON_URL}/metrics/{chakra}", timeout=5)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    value = float(data.get("value", 0.0))
    if value <= threshold:
        return False

    subprocess.run([str(script_path)], check=True)

    timestamp = datetime.utcnow().isoformat() + "Z"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} {chakra} {value}\n")

    QUARANTINE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with QUARANTINE_LOG.open("a", encoding="utf-8") as qlog:
        qlog.write(f"| {timestamp} | {chakra} | healed | {value} |\n")

    return True


async def listen_for_heartbeat(
    chakra: str, agent_id: str, subcomponents: Iterable[str] | None = None
) -> None:
    """Listen for heartbeat events and confirm receipt for ``chakra``.

    ``subcomponents`` allows forwarding confirmations to nested components
    associated with the chakra service.
    """

    async def _handle(event: Event) -> None:
        if event.event_type == "heartbeat" and event.payload.get("chakra") == chakra:
            emit_event(agent_id, "pulse_confirmation", {"chakra": chakra})
            for sub in subcomponents or []:
                emit_event(sub, "pulse_confirmation", {"chakra": chakra})

    await subscribe(_handle)


__all__ = [
    "heal",
    "listen_for_heartbeat",
    "CHAKRACON_URL",
    "LOG_PATH",
    "QUARANTINE_LOG",
]
