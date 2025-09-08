"""Connector mixins and base classes."""

from __future__ import annotations

__version__ = "0.2.0"

import threading
import time
from typing import Any, Dict

from .signal_bus import publish, subscribe


class ConnectorHeartbeat:
    """Mixin emitting heartbeats and alerting on missed pulses.

    Parameters
    ----------
    channel:
        Base chakra name for the connector.
    interval:
        Seconds between heartbeats.
    miss_threshold:
        Number of missed heartbeats before publishing an alert.
    """

    def __init__(
        self, channel: str, *, interval: float = 30.0, miss_threshold: int = 3
    ) -> None:
        self._channel = channel
        self._interval = interval
        self._miss_threshold = miss_threshold
        self._stop = threading.Event()
        self._send_enabled = True
        self._last_seen = time.monotonic()
        self._cycle = 0
        self._lock = threading.Lock()
        self._unsubscribe = subscribe(f"{self._channel}:heartbeat", self._on_heartbeat)
        self._sender = threading.Thread(target=self._send_loop, daemon=True)
        self._monitor = threading.Thread(target=self._monitor_loop, daemon=True)

    # public API -----------------------------------------------------------
    def start(self) -> None:
        """Start heartbeat emission and monitoring."""
        self._sender.start()
        self._monitor.start()

    def stop(self) -> None:
        """Stop heartbeat threads and unsubscribe."""
        self._stop.set()
        self._sender.join()
        self._monitor.join()
        self._unsubscribe()

    def pause(self) -> None:
        """Pause heartbeat emissions."""
        self._send_enabled = False

    def resume(self) -> None:
        """Resume heartbeat emissions."""
        self._send_enabled = True

    # internal helpers -----------------------------------------------------
    def _on_heartbeat(self, _payload: Dict[str, Any]) -> None:
        with self._lock:
            self._last_seen = time.monotonic()

    def _send_loop(self) -> None:
        while not self._stop.wait(self._interval):
            if self._send_enabled:
                self._cycle += 1
                publish(
                    f"{self._channel}:heartbeat",
                    {"channel": self._channel},
                    self._cycle,
                )

    def _monitor_loop(self) -> None:
        while not self._stop.wait(self._interval):
            with self._lock:
                elapsed = time.monotonic() - self._last_seen
            if elapsed > self._interval * self._miss_threshold:
                publish(
                    f"{self._channel}:alert",
                    {"channel": self._channel},
                    self._cycle,
                )
                with self._lock:
                    self._last_seen = time.monotonic()


__all__ = ["ConnectorHeartbeat"]
