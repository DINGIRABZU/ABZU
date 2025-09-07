"""Stream self-healing ledger updates via WebSocket."""

from __future__ import annotations

import json
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .self_healing_ledger import SelfHealingLedger

router = APIRouter()
ledger = SelfHealingLedger()
_clients: Set[WebSocket] = set()


async def broadcast_update(event: Dict[str, Any]) -> None:
    """Send ``event`` to all connected WebSocket clients."""
    message = json.dumps(event)
    for ws in set(_clients):
        try:
            await ws.send_text(message)
        except Exception:
            _clients.discard(ws)


@router.websocket("/self-healing/updates")
async def self_healing_updates(websocket: WebSocket) -> None:
    """WebSocket channel streaming self-healing ledger events."""
    await websocket.accept()
    _clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.discard(websocket)


__all__ = ["router", "ledger", "broadcast_update"]
