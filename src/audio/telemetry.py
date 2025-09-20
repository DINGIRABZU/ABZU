"""Lightweight telemetry collector for audio instrumentation."""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List


def _normalize(value: Any) -> Any:
    """Return ``value`` converted into a JSON-serialisable representation."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalize(v) for v in value]
    return str(value)


class TelemetryCollector:
    """Simple in-memory telemetry collector with structured logging output."""

    def __init__(self, logger_name: str = "abzu.telemetry.audio") -> None:
        self._logger = logging.getLogger(logger_name)
        self._events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def emit(self, event: str, **fields: Any) -> None:
        """Record a telemetry ``event`` with optional ``fields``."""

        payload: Dict[str, Any] = {"event": event, "timestamp": time.time()}
        for key, value in fields.items():
            payload[key] = _normalize(value)

        message = json.dumps(payload, sort_keys=True)
        self._logger.info("telemetry=%s", message)
        with self._lock:
            self._events.append(payload)

    def get_events(self) -> List[Dict[str, Any]]:
        """Return a snapshot of recorded telemetry events."""

        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        """Remove all stored telemetry events."""

        with self._lock:
            self._events.clear()


telemetry = TelemetryCollector()


__all__ = ["TelemetryCollector", "telemetry"]
