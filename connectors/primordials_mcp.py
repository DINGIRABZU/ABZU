"""MCP wrapper for Primordials metrics.

This connector communicates with the MCP gateway to register
context and forward metrics to the Primordials service.

- **Endpoints:** ``POST /context/register``, ``POST /primordials/metrics``
- **Auth:** Optional via MCP gateway configuration
- **Linked services:** Primordials
"""

from __future__ import annotations

__version__ = "0.1.0"

import os
from typing import Any, Mapping

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


async def send_metrics(metrics: Mapping[str, Any]) -> dict[str, str]:
    """Send ``metrics`` to the Primordials service via the MCP gateway."""
    if not _USE_MCP:
        raise RuntimeError("MCP is not enabled")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_MCP_URL}/primordials/metrics",
            json=dict(metrics),
            timeout=5.0,
        )
        resp.raise_for_status()
        return resp.json()


__all__ = ["handshake", "send_metrics"]
