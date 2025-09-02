from __future__ import annotations


"""HTTP API for logging and retrieving persistent stories.

- **Endpoints:** ``POST /story``, ``GET /story/log``, ``GET /story/stream``
- **Auth:** Bearer token
- **Linked service:** vector_memory
"""

__version__ = "0.2.0"

import json
from typing import Iterable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from memory import narrative_engine

router = APIRouter()


class Story(BaseModel):
    """Request body for logging a story."""

    text: str


@router.post("/story")
def log_story(story: Story) -> dict[str, str]:
    """Persist ``story`` text to the narrative store."""

    narrative_engine.log_story(story.text)
    return {"status": "ok"}


@router.get("/story/log")
def story_log(limit: int = 100) -> dict[str, object]:
    """Return recorded stories."""

    stories = list(narrative_engine.stream_stories())[:limit]
    return {"stories": stories}


@router.get("/story/stream")
def story_stream(limit: int = 100) -> StreamingResponse:
    """Stream recorded stories as JSON lines."""

    stories = list(narrative_engine.stream_stories())[:limit]

    def _gen() -> Iterable[str]:
        for text in stories:
            yield json.dumps({"story": text}) + "\n"

    return StreamingResponse(_gen(), media_type="application/json")


__all__ = ["router"]
