"""Security canary for intrusion monitoring.

Provides a simple interface to react to breach indicators by
persisting a memory snapshot and broadcasting an alert message.
"""

from __future__ import annotations

__version__ = "0.1.0"

import logging
import threading
import time

import requests
from pathlib import Path
from typing import Callable

from vector_memory import persist_snapshot
from ..event_bus import emit_event

logger = logging.getLogger(__name__)

CHAKRA = "sacral"
CHAKRACON_URL = "http://localhost:8080"
THRESHOLD_THREAT = 0.5


def fetch_metrics() -> dict:
    resp = requests.get(f"{CHAKRACON_URL}/metrics/{CHAKRA}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def monitor_metrics(poll_interval: float = 5.0) -> None:
    while True:
        data = fetch_metrics()
        value = data.get("threat", 0.0)
        if value > THRESHOLD_THREAT:
            emit_event("victim", "threat_high", {"value": value})
        time.sleep(poll_interval)


def start_monitoring(poll_interval: float = 5.0) -> threading.Thread:
    thread = threading.Thread(
        target=monitor_metrics, args=(poll_interval,), daemon=True
    )
    thread.start()
    return thread


def broadcast_alert(message: str) -> None:
    """Broadcast a security alert ``message`` via logging."""

    logger.error("SECURITY ALERT: %s", message)


def detect_breach(
    breached: bool,
    *,
    snap_func: Callable[[], Path] | None = None,
    alert: Callable[[str], None] | None = None,
) -> bool:
    """Trigger a snapshot and alert when a breach is detected.

    Returns ``True`` if a breach was handled.
    """

    if not breached:
        return False

    snapper = snap_func or persist_snapshot
    path = snapper()
    (alert or broadcast_alert)(f"breach detected, snapshot stored at {path}")
    return True


__all__ = ["detect_breach", "broadcast_alert", "start_monitoring"]
