"""FastAPI server providing video generation and avatar streaming APIs."""

from __future__ import annotations

from typing import List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from prometheus_fastapi_instrumentator import Instrumentator

from style_engine import style_library

app = FastAPI()

Instrumentator().instrument(app).expose(app)

# ---------------------------------------------------------------------------
# Core logic functions

_connections: Set[WebSocket] = set()


async def generate_video(prompt: str) -> dict[str, str]:
    """Queue a placeholder video generation request."""
    return {"status": "queued", "prompt": prompt}


async def list_styles() -> List[str]:
    """Return available style names from the styles directory."""
    return [p.stem for p in style_library.STYLES_DIR.glob("*.yaml")]


async def broadcast_avatar_update(update: str) -> None:
    """Send ``update`` to all connected avatar websocket clients."""
    for ws in set(_connections):
        try:
            await ws.send_text(update)
        except RuntimeError:
            _connections.discard(ws)


# ---------------------------------------------------------------------------
# API endpoints


@app.post("/generate_video")  # type: ignore[misc]
async def generate_video_endpoint(data: dict[str, str]) -> dict[str, str]:
    """Endpoint to queue a video generation request."""
    prompt = data.get("prompt", "")
    return await generate_video(prompt)


@app.websocket("/stream_avatar")  # type: ignore[misc]
async def stream_avatar(websocket: WebSocket) -> None:
    """Open a websocket for real-time avatar updates."""
    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await broadcast_avatar_update(data)
    except WebSocketDisconnect:
        _connections.discard(websocket)


@app.get("/styles")  # type: ignore[misc]
async def styles_endpoint() -> dict[str, List[str]]:
    """Return available style configuration names."""
    return {"styles": await list_styles()}


__all__ = ["app", "generate_video", "list_styles", "broadcast_avatar_update"]
