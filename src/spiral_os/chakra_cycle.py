"""Generate chakra cycles and expose heartbeat metrics.

This module defines gear ratios for each chakra and a scheduler that updates
Prometheus gauges representing the current cycle phase.  The
:class:`ChakraCycle` can be polled manually via :meth:`emit` or run in a
background thread using :meth:`start`.
"""

from __future__ import annotations

import time
from threading import Event, Thread
from typing import Dict, Mapping

try:  # pragma: no cover - optional dependency
    from prometheus_client import Gauge
except Exception:  # pragma: no cover - optional dependency
    Gauge = None  # type: ignore[assignment]

__version__ = "0.1.0"

GEAR_RATIOS: Dict[str, int] = {
    "root": 1,
    "sacral": 2,
    "solar": 3,
    "heart": 5,
    "throat": 8,
    "third_eye": 13,
    "crown": 21,
}
"""Gear ratios for each chakra used to compute heartbeat cycles."""

HEARTBEAT_GAUGE = (
    Gauge("chakra_heartbeat", "Normalized chakra heartbeat phase", ["chakra"])
    if Gauge is not None
    else None
)


class ChakraCycle:
    """Scheduler that emits heartbeat metrics for chakra alignment."""

    def __init__(
        self,
        ratios: Mapping[str, int] | None = None,
        *,
        interval: float = 1.0,
    ) -> None:
        self.ratios = dict(ratios or GEAR_RATIOS)
        self.interval = interval
        self._stop = Event()
        self._thread: Thread | None = None

    # ------------------------------------------------------------------
    def emit(self) -> Dict[str, float]:
        """Return current cycle phase for each chakra and update gauges."""
        now = time.time()
        metrics: Dict[str, float] = {}
        for name, ratio in self.ratios.items():
            phase = (now * ratio) % 1.0
            metrics[name] = phase
            if HEARTBEAT_GAUGE is not None:
                HEARTBEAT_GAUGE.labels(name).set(phase)  # type: ignore[call-arg]
        return metrics

    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop.is_set():
            self.emit()
            self._stop.wait(self.interval)

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start emitting heartbeat metrics on a background thread."""
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear()
            self._thread = Thread(target=self._run, daemon=True)
            self._thread.start()

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop the background heartbeat thread."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval)


__all__ = ["ChakraCycle", "GEAR_RATIOS"]
