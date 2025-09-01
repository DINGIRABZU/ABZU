"""HTTP API for retrieving Bana narratives and memory metadata."""

__version__ = "0.1.1"

import json
from typing import Iterable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from memory import narrative_engine

router = APIRouter()


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
