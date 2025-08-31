from __future__ import annotations


"""HTTP API for retrieving stored narratives and memory metadata."""

__version__ = "0.1.0"

import json
from typing import Iterable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import corpus_memory_logging
import vector_memory

router = APIRouter()


@router.get("/story/log")
def story_log(limit: int = 100) -> dict[str, object]:
    """Return recorded narratives and memory metadata.

    Parameters
    ----------
    limit:
        Maximum number of narrative entries to return. ``None`` returns all
        available entries.
    """

    narratives = corpus_memory_logging.load_interactions(limit)
    store = vector_memory._get_store()
    return {"narratives": narratives, "memory": store.metadata}


@router.get("/story/stream")
def story_stream(limit: int = 100) -> StreamingResponse:
    """Stream narratives followed by memory metadata as JSON lines."""

    narratives = corpus_memory_logging.load_interactions(limit)
    store = vector_memory._get_store()

    def _gen() -> Iterable[str]:
        for entry in narratives:
            yield json.dumps({"narrative": entry}) + "\n"
        yield json.dumps({"memory": store.metadata}) + "\n"

    return StreamingResponse(_gen(), media_type="application/json")


__all__ = ["router"]
