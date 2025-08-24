"""Network monitoring utilities."""

from __future__ import annotations

import threading

from .analysis import analyze_capture
from .capture import capture_packets
from .config import CONFIG_FILE, load_config


def schedule_capture(interface: str, period: float) -> threading.Timer:
    """Capture packets from ``interface`` every ``period`` seconds.

    The returned timer represents the next scheduled run. Each invocation
    schedules a new timer, allowing captures to continue indefinitely until the
    process exits.
    """

    def _run() -> None:
        capture_packets(interface)
        schedule_capture(interface, period)

    timer = threading.Timer(period, _run)
    timer.daemon = True
    timer.start()
    return timer


__all__ = [
    "capture_packets",
    "analyze_capture",
    "load_config",
    "schedule_capture",
    "CONFIG_FILE",
]
