"""Minimal MCP-based connector example.

This module illustrates how a connector can interact with the Model Context
Protocol (MCP) gateway using a simple request/response flow while still
leveraging the internal signal bus for publish/subscribe messaging.

- **Endpoints:** ``POST /model/invoke`` (MCP gateway)
- **Auth:** Optional via MCP gateway configuration
- **Linked services:** internal models
"""

from __future__ import annotations

__version__ = "0.1.0"

import os
from typing import Any, Callable, Dict

import httpx

from .signal_bus import publish, subscribe

_USE_MCP = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")


async def invoke(model: str, text: str) -> Dict[str, Any]:
    """Invoke ``model`` with ``text`` via the MCP gateway."""
    if not _USE_MCP:
        raise RuntimeError("MCP is not enabled")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_MCP_URL}/model/invoke",
            json={"model": model, "text": text},
            timeout=5.0,
        )
        resp.raise_for_status()
        return resp.json()


def publish_event(chakra: str, payload: Dict[str, Any]) -> None:
    """Publish ``payload`` tagged with ``chakra`` on the signal bus."""
    publish(chakra, payload)


def subscribe_events(
    chakra: str, callback: Callable[[Dict[str, Any]], None]
) -> Callable[[], None]:
    """Subscribe ``callback`` to events for ``chakra``."""
    return subscribe(chakra, callback)


__all__ = ["invoke", "publish_event", "subscribe_events"]
