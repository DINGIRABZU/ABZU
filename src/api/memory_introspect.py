"""Memory introspection endpoints."""

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException

__all__ = ["router"]
__version__ = "0.1.0"

router = APIRouter(prefix="/memory", tags=["memory"])

_API_TOKEN = os.getenv("MEMORY_API_TOKEN", "secret")


def _authorize(token: str | None) -> None:
    if token != _API_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/query")
async def query_memory(
    q: str | None = None,
    x_api_key: str | None = Header(None),
) -> Dict[str, Any]:
    """Return memory metrics or search results."""
    _authorize(x_api_key)
    if q:
        return {"results": [f"stub result for {q}"]}
    chakras = {
        "root": {"count": 0, "last_heartbeat": 0},
        "crown": {"count": 0, "last_heartbeat": 0},
    }
    return {"chakras": chakras}


@router.post("/purge")
async def purge_memory(
    chakra: str,
    x_api_key: str | None = Header(None),
) -> Dict[str, str]:
    """Purge memory for ``chakra`` (stub)."""
    _authorize(x_api_key)
    return {"purged": chakra}


@router.post("/snapshot")
async def snapshot_memory(
    x_api_key: str | None = Header(None),
) -> Dict[str, str]:
    """Create a memory snapshot (stub)."""
    _authorize(x_api_key)
    return {"status": "snapshotted"}
