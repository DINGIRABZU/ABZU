"""Cocytus prompt arbitration utilities.

Responsibilities:
- logical sanitization
- legal parsing
- audit model bias
"""

from __future__ import annotations

import threading
import time

import requests

from typing import Any, Dict

from ..event_bus import emit_event

__version__ = "0.1.0"

CHAKRA = "solar_plexus"
CHAKRACON_URL = "http://localhost:8080"
THRESHOLD_BIAS = 0.7


def fetch_metrics() -> Dict[str, Any]:
    resp = requests.get(f"{CHAKRACON_URL}/metrics/{CHAKRA}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def monitor_metrics(poll_interval: float = 5.0) -> None:
    while True:
        data = fetch_metrics()
        value = float(data.get("bias", 0.0))
        if value > THRESHOLD_BIAS:
            emit_event("cocytus", "bias_high", {"value": value})
        time.sleep(poll_interval)


def start_monitoring(poll_interval: float = 5.0) -> threading.Thread:
    thread = threading.Thread(
        target=monitor_metrics, args=(poll_interval,), daemon=True
    )
    thread.start()
    return thread


def arbitrate(actor: str, action: str, entity_eval: Dict[str, Any]) -> None:
    """Escalate a non-compliant action for Cocytus arbitration."""

    emit_event(
        "cocytus",
        "arbitration",
        {"actor": actor, "action": action, "entity": entity_eval},
    )


__all__ = ["arbitrate", "start_monitoring"]
