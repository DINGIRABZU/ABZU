"""HTTP API for retrieving Bana narratives and memory metadata."""

__version__ = "0.1.1"

import json
import time
from typing import Iterable, Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from memory import narrative_engine
from . import narrative

try:  # pragma: no cover - optional dependency
    from prometheus_client import Gauge, REGISTRY
except Exception:  # pragma: no cover - optional dependency
    Gauge = REGISTRY = None  # type: ignore[assignment]

_START_TIME = time.perf_counter()

if Gauge is not None and REGISTRY is not None:
    if "service_boot_duration_seconds" in REGISTRY._names_to_collectors:
        BOOT_DURATION_GAUGE = REGISTRY._names_to_collectors[
            "service_boot_duration_seconds"
        ]  # type: ignore[assignment]
    else:
        BOOT_DURATION_GAUGE = Gauge(
            "service_boot_duration_seconds",
            "Duration of service startup in seconds",
            ["service"],
        )
else:
    BOOT_DURATION_GAUGE = None

router = APIRouter()

if BOOT_DURATION_GAUGE is not None:
    BOOT_DURATION_GAUGE.labels("bana").set(time.perf_counter() - _START_TIME)


class StoryEvent(BaseModel):
    """Input model for ``POST /story``."""

    agent_id: str
    event_type: str
    payload: dict[str, Any]
    time: str | None = None
    target_agent: str | None = None


@router.post("/story")
def log_story(event: StoryEvent) -> dict[str, str]:
    """Validate and dispatch a narrative event."""

    narrative.emit(
        event.agent_id,
        event.event_type,
        event.payload,
        timestamp=event.time,
        target_agent=event.target_agent,
    )
    return {"status": "ok"}


@router.get("/story/log")
def story_log(limit: int = 100) -> dict[str, object]:
    """Return structured narrative events."""

    events = list(narrative_engine.query_events())[:limit]
    return {"events": events}


@router.get("/story/stream")
def story_stream(limit: int = 100) -> StreamingResponse:
    """Stream narrative events as JSON lines."""

    events = list(narrative_engine.query_events())[:limit]

    def _gen() -> Iterable[str]:
        for event in events:
            yield json.dumps(event) + "\n"

    return StreamingResponse(_gen(), media_type="application/json")


__all__ = ["router"]
