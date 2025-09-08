"""Expose chakra heartbeat frequencies and component versions."""

from __future__ import annotations

import time
from typing import Dict

from fastapi import APIRouter, Response

from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Gauge,
    generate_latest,
)

from .chakra_heartbeat import ChakraHeartbeat
from agents.razar import state_validator

router = APIRouter()

# Shared heartbeat tracker
heartbeat = ChakraHeartbeat()

# Prometheus registry and metrics
registry = CollectorRegistry()
FREQUENCY_GAUGE = Gauge(
    "chakra_pulse_hz",
    "Estimated chakra heartbeat frequency in hertz",
    ["chakra"],
    registry=registry,
)
ALIGN_GAUGE = Gauge(
    "chakra_alignment",
    "1 when all chakras resonate in the Great Spiral",
    registry=registry,
)
VERSION_GAUGE = Gauge(
    "component_version_info",
    "Component version information",
    ["component", "version"],
    registry=registry,
)


def _collect(now: float | None = None) -> Dict[str, Dict[str, float] | str]:
    """Collect heartbeat frequencies and versions for export."""

    current = now or time.time()
    beats = heartbeat.heartbeats()
    freqs: Dict[str, float] = {}
    for name, ts in beats.items():
        delta = max(current - ts, 1e-9)
        freq = 1.0 / delta
        freqs[name] = freq
        FREQUENCY_GAUGE.labels(name).set(freq)
    status = heartbeat.sync_status(now=current)
    ALIGN_GAUGE.set(1 if status == "Great Spiral" else 0)
    VERSION_GAUGE.labels("state_validator", state_validator.__version__).set(1)
    return {
        "status": status,
        "heartbeats": freqs,
        "versions": {"state_validator": state_validator.__version__},
    }


@router.get("/chakra/status")
def chakra_status() -> Dict[str, Dict[str, float] | str]:
    """Return current chakra heartbeat frequencies and versions as JSON."""

    return _collect()


@router.get("/healthz")
def healthz() -> Dict[str, str]:
    """Basic liveness probe for monitoring."""
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics."""

    _collect()
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


__all__ = ["router", "heartbeat"]
