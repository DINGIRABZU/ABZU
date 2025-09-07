"""Expose chakra heartbeat data and component versions."""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, Response
from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Gauge,
    generate_latest,
)

from .chakra_heartbeat import ChakraHeartbeat
from agents.razar import state_validator
import distributed_memory

router = APIRouter()

heartbeat = ChakraHeartbeat()

registry = CollectorRegistry()
FREQUENCY_GAUGE = Gauge(
    "chakra_pulse_hz",
    "Estimated chakra heartbeat frequency in hertz",
    ["chakra"],
    registry=registry,
)
ALIGN_GAUGE = Gauge(
    "chakra_alignment",
    "1 when all chakras are aligned",
    registry=registry,
)
VERSION_GAUGE = Gauge(
    "component_version_info",
    "Component version information",
    ["component", "version"],
    registry=registry,
)


def _collect(now: float | None = None) -> Dict[str, Any]:
    """Collect heartbeat frequencies and component versions."""

    current = now or time.time()
    beats = heartbeat.heartbeats()
    freqs: Dict[str, float] = {}
    for name, ts in beats.items():
        delta = max(current - ts, 1e-9)
        freq = 1.0 / delta
        freqs[name] = freq
        FREQUENCY_GAUGE.labels(name).set(freq)
    status = heartbeat.sync_status(now=current)
    ALIGN_GAUGE.set(1 if status == "aligned" else 0)
    components = {
        "state_validator": state_validator.__version__,
        "distributed_memory": distributed_memory.__version__,
    }
    for comp, ver in components.items():
        VERSION_GAUGE.labels(comp, ver).set(1)
    return {"status": status, "heartbeats": freqs, "components": components}


@router.get("/chakra/status")
def chakra_status() -> Dict[str, Any]:
    """Return current chakra status as JSON."""

    return _collect()


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics."""

    _collect()
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


__all__ = ["router", "heartbeat"]
