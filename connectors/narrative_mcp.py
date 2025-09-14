"""MCP wrapper for narrative logging.

This connector uses the MCP gateway to register context and log
stories to the narrative service.

- **Endpoints:** ``POST /context/register``, ``POST /narrative/story``
- **Auth:** Optional via MCP gateway configuration
- **Linked services:** vector_memory
"""

from __future__ import annotations

__version__ = "0.1.0"

import os
from typing import Any

import httpx

_USE_MCP = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")


async def handshake(id: str, data: dict[str, Any] | None = None) -> dict[str, str]:
    """Register connector ``id`` with optional ``data`` at the MCP gateway."""
    if not _USE_MCP:
        raise RuntimeError("MCP is not enabled")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_MCP_URL}/context/register",
            json={"id": id, "data": data or {}},
            timeout=5.0,
        )
        resp.raise_for_status()
        return resp.json()


async def log_story(text: str) -> dict[str, str]:
    """Persist ``text`` to the narrative store via the MCP gateway."""
    if not _USE_MCP:
        raise RuntimeError("MCP is not enabled")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_MCP_URL}/narrative/story",
            json={"text": text},
            timeout=5.0,
        )
        resp.raise_for_status()
        return resp.json()


__all__ = ["handshake", "log_story"]
