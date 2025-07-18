"""Network monitoring utilities."""
from __future__ import annotations

from pathlib import Path
import json
from importlib import resources
import threading

from typing import Optional

CONFIG_FILE = Path(__file__).resolve().parents[2] / "INANNA_AI_AGENT" / "network_utils_config.json"

_DEFAULT_CONFIG = {"log_dir": "network_logs", "capture_file": "network_logs/capture.pcap"}


def load_config() -> dict:
    """Return configuration for network utilities."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())

    try:
        resource_path = resources.files("INANNA_AI") / "network_utils_config.json"
        if resource_path.is_file():
            return json.loads(resource_path.read_text())
    except Exception:
        pass

    return _DEFAULT_CONFIG.copy()


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


from .capture import capture_packets
from .analysis import analyze_capture

__all__ = [
    "capture_packets",
    "analyze_capture",
    "load_config",
    "schedule_capture",
    "CONFIG_FILE",
]
