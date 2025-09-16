"""Lightweight Prometheus metrics for RAZAR AI handovers."""

from __future__ import annotations

import logging
import os
from threading import Lock
from typing import Any

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, start_http_server
except Exception:  # pragma: no cover - optional dependency
    Counter = None  # type: ignore[assignment]
    start_http_server = None  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)

_SUCCESS_COUNTER: Any = None
_FAILURE_COUNTER: Any = None
_RETRY_COUNTER: Any = None
_LOCK = Lock()
_INITIALIZED = False
_SERVER_STARTED = False

__all__ = ["init_metrics", "record_invocation"]


def _resolve_port(port: int | None) -> int:
    """Return the metrics port honoring the ``RAZAR_METRICS_PORT`` override."""

    if port is not None:
        return port

    env_value = os.getenv("RAZAR_METRICS_PORT")
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            LOGGER.warning(
                "Invalid RAZAR_METRICS_PORT=%s; defaulting to 9360", env_value
            )
    return 9360


def init_metrics(port: int | None = None) -> bool:
    """Initialise counters and expose them via an HTTP endpoint."""

    global _INITIALIZED, _SERVER_STARTED
    global _SUCCESS_COUNTER, _FAILURE_COUNTER, _RETRY_COUNTER
    if Counter is None or start_http_server is None:
        LOGGER.debug("prometheus_client not available; metrics disabled")
        return False

    with _LOCK:
        if _INITIALIZED:
            return _SERVER_STARTED

        _SUCCESS_COUNTER = Counter(
            "razar_ai_invocation_success_total",
            "Count of AI handover attempts that produced a patch",
            ["component"],
        )
        _FAILURE_COUNTER = Counter(
            "razar_ai_invocation_failure_total",
            "Count of AI handover attempts that produced no patch",
            ["component"],
        )
        _RETRY_COUNTER = Counter(
            "razar_ai_invocation_retries_total",
            "Total retries performed across AI handover attempts",
            ["component"],
        )

        port_value = _resolve_port(port)
        started = False
        try:
            start_http_server(port_value)
        except OSError as exc:  # pragma: no cover - platform dependent
            LOGGER.warning(
                "Could not start metrics server on port %s: %s", port_value, exc
            )
        else:
            started = True
            LOGGER.info("RAZAR metrics exposed on port %s", port_value)

        _INITIALIZED = True
        _SERVER_STARTED = started
        return started


def record_invocation(component: str, success: bool, *, retries: int = 0) -> None:
    """Increment counters for a single handover attempt."""

    success_counter = _SUCCESS_COUNTER
    failure_counter = _FAILURE_COUNTER
    retry_counter = _RETRY_COUNTER
    if success_counter is None or failure_counter is None or retry_counter is None:
        return

    label = (component or "unknown").lower()
    labels = {"component": label}
    if success:
        success_counter.labels(**labels).inc()
    else:
        failure_counter.labels(**labels).inc()

    if retries > 0:
        retry_counter.labels(**labels).inc(retries)
