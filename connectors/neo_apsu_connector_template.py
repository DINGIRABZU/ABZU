"""Neo-APSU connector template.

Demonstrates an MCP handshake, heartbeat emission, and doctrine compliance
checks for new connectors.
"""

from __future__ import annotations

__version__ = "0.1.0"

import os
from typing import Any

import httpx

_USE_MCP = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")


async def handshake() -> None:
    """Perform the initial MCP handshake with the gateway."""
    if not _USE_MCP:
        raise RuntimeError("MCP is not enabled")
    async with httpx.AsyncClient() as client:
        # Exchange capabilities with the gateway.
        resp = await client.post(f"{_MCP_URL}/handshake", timeout=5.0)
        resp.raise_for_status()


async def send_heartbeat(payload: dict[str, Any]) -> None:
    """Emit heartbeat telemetry to maintain alignment."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{_MCP_URL}/heartbeat", json=payload, timeout=5.0)
        resp.raise_for_status()


def doctrine_compliant() -> bool:
    """Return True when the connector satisfies doctrine requirements."""
    # Insert doctrine verification logic here.
    return True


__all__ = ["handshake", "send_heartbeat", "doctrine_compliant"]
