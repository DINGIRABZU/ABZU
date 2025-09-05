"""HTTP API for logging and retrieving persistent stories.

- **Endpoints:** ``POST /story``, ``GET /story/log``, ``GET /story/stream``
- **Auth:** Bearer token
- **Linked service:** vector_memory
"""

from __future__ import annotations


__version__ = "0.2.0"

import json
import time
from typing import Iterable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from memory import narrative_engine, story_lookup

router = APIRouter()

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Gauge, REGISTRY
except Exception:  # pragma: no cover - optional dependency
    Counter = Gauge = REGISTRY = None  # type: ignore[assignment]

_START_TIME = time.perf_counter()

if Gauge is not None and REGISTRY is not None:
    if "service_boot_duration_seconds" in REGISTRY._names_to_collectors:
        BOOT_DURATION_GAUGE = REGISTRY._names_to_collectors["service_boot_duration_seconds"]  # type: ignore[assignment]
    else:
        BOOT_DURATION_GAUGE = Gauge(
            "service_boot_duration_seconds",
            "Duration of service startup in seconds",
            ["service"],
        )
else:
    BOOT_DURATION_GAUGE = None

if Counter is not None and REGISTRY is not None:
    if "narrative_events_total" in REGISTRY._names_to_collectors:
        NARRATIVE_THROUGHPUT = REGISTRY._names_to_collectors["narrative_events_total"]  # type: ignore[assignment]
    else:
        NARRATIVE_THROUGHPUT = Counter(
            "narrative_events_total",
            "Total number of narrative events logged",
        )
    if "narrative_throughput_total" in REGISTRY._names_to_collectors:
        THROUGHPUT_COUNTER = REGISTRY._names_to_collectors["narrative_throughput_total"]  # type: ignore[assignment]
    else:
        THROUGHPUT_COUNTER = Counter(
            "narrative_throughput_total",
            "Narrative events processed",
            ["service"],
        )
    if "service_errors_total" in REGISTRY._names_to_collectors:
        ERROR_COUNTER = REGISTRY._names_to_collectors["service_errors_total"]  # type: ignore[assignment]
    else:
        ERROR_COUNTER = Counter(
            "service_errors_total",
            "Number of errors encountered",
            ["service"],
        )
else:
    NARRATIVE_THROUGHPUT = THROUGHPUT_COUNTER = ERROR_COUNTER = None

if BOOT_DURATION_GAUGE is not None:
    BOOT_DURATION_GAUGE.labels("bana").set(time.perf_counter() - _START_TIME)


class Story(BaseModel):
    """Request body for logging a story."""

    text: str


@router.post("/story")
def log_story(story: Story) -> dict[str, str]:
    """Persist ``story`` text to the narrative store."""
    try:
        narrative_engine.log_story(story.text)
        if NARRATIVE_THROUGHPUT is not None:
            NARRATIVE_THROUGHPUT.inc()
        if THROUGHPUT_COUNTER is not None:
            THROUGHPUT_COUNTER.labels("bana").inc()
        return {"status": "ok"}
    except Exception:
        if ERROR_COUNTER is not None:
            ERROR_COUNTER.labels("bana").inc()
        raise


@router.get("/story/log")
def story_log(limit: int = 100) -> dict[str, object]:
    """Return recorded stories."""
    try:
        stories = list(narrative_engine.stream_stories())[:limit]
        return {"stories": stories}
    except Exception:
        if ERROR_COUNTER is not None:
            ERROR_COUNTER.labels("bana").inc()
        raise


@router.get("/story/stream")
def story_stream(limit: int = 100) -> StreamingResponse:
    """Stream recorded stories as JSON lines."""
    try:
        stories = list(narrative_engine.stream_stories())[:limit]

        def _gen() -> Iterable[str]:
            for text in stories:
                yield json.dumps({"story": text}) + "\n"

        return StreamingResponse(_gen(), media_type="application/json")
    except Exception:
        if ERROR_COUNTER is not None:
            ERROR_COUNTER.labels("bana").inc()
        raise


@router.get("/narrative/search")
def narrative_search(
    agent_id: str | None = None,
    event_type: str | None = None,
    text: str | None = None,
) -> dict[str, object]:
    """Return indexed stories with matching event payloads."""

    try:
        results = list(
            story_lookup.find(agent_id=agent_id, event_type=event_type, text=text)
        )
        return {"results": results}
    except Exception:
        if ERROR_COUNTER is not None:
            ERROR_COUNTER.labels("bana").inc()
        raise


__all__ = ["router"]
