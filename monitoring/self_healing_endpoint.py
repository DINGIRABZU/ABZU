"""Expose self-healing ledger snapshots and stream updates."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .self_healing_ledger import SelfHealingLedger

router = APIRouter()
_clients: Set[WebSocket] = set()


async def broadcast_update(event: Dict[str, Any]) -> None:
    """Send ``event`` to all connected WebSocket clients."""
    message = json.dumps(event)
    for ws in set(_clients):
        try:
            await ws.send_text(message)
        except Exception:
            _clients.discard(ws)


ledger = SelfHealingLedger(on_event=lambda e: asyncio.create_task(broadcast_update(e)))


@router.get("/self-healing/ledger")
def get_ledger() -> Dict[str, Any]:
    """Return full ledger and currently active repairs."""

    return {"ledger": ledger.read_entries(), "active": ledger.active_repairs()}


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
