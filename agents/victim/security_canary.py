"""Security canary for intrusion monitoring.

Provides a simple interface to react to breach indicators by
persisting a memory snapshot and broadcasting an alert message.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from vector_memory import persist_snapshot

logger = logging.getLogger(__name__)


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


__all__ = ["detect_breach", "broadcast_alert"]
