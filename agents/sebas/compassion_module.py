"""Responsibilities:
- empathy modeling
- emotional safety buffer
- conflict signal resolution
"""

import threading
import time

import requests

from ..event_bus import emit_event

__version__ = "0.1.0"

CHAKRA = "heart"
CHAKRACON_URL = "http://localhost:8080"
THRESHOLD_STRESS = 0.8


def fetch_metrics() -> dict:
    resp = requests.get(f"{CHAKRACON_URL}/metrics/{CHAKRA}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def monitor_metrics(poll_interval: float = 5.0) -> None:
    while True:
        data = fetch_metrics()
        value = data.get("stress", 0.0)
        if value > THRESHOLD_STRESS:
            emit_event("sebas", "stress_high", {"value": value})
        time.sleep(poll_interval)


def start_monitoring(poll_interval: float = 5.0) -> threading.Thread:
    thread = threading.Thread(
        target=monitor_metrics, args=(poll_interval,), daemon=True
    )
    thread.start()
    return thread


__all__ = ["start_monitoring"]
