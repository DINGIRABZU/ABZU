"""FastAPI server providing video generation and avatar streaming APIs."""

from __future__ import annotations

from typing import List, Set, cast

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pathlib import Path

from audio.voice_cloner import VoiceCloner
from prometheus_fastapi_instrumentator import Instrumentator

from style_engine import style_library

app = FastAPI()

Instrumentator().instrument(app).expose(app)

# ---------------------------------------------------------------------------
# Core logic functions

_connections: Set[WebSocket] = set()
voice_cloner = VoiceCloner()


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


@app.post("/voice/capture")  # type: ignore[misc]
async def capture_voice(data: dict[str, object]) -> dict[str, str]:
    """Record a short voice sample for a speaker profile."""

    path = Path(str(data.get("path", "sample.wav")))
    seconds = float(cast(float | int | str, data.get("seconds", 3.0)))
    sr = int(cast(float | int | str, data.get("sr", 22_050)))
    speaker = str(data.get("speaker", "user"))
    try:
        voice_cloner.capture_sample(path, seconds=seconds, sr=sr, speaker=speaker)
    except RuntimeError as exc:
        return {"error": str(exc)}
    return {"sample": str(path), "speaker": speaker}


@app.post("/voice/synthesize")  # type: ignore[misc]
async def synthesize_voice(data: dict[str, object]) -> dict[str, object]:
    """Generate speech for ``text`` with a cloned voice."""

    text = str(data.get("text", ""))
    out_path = Path(str(data.get("out", "speech.wav")))
    speaker = str(data.get("speaker", "user"))
    emotion = str(data.get("emotion", "neutral"))
    try:
        _, mos = voice_cloner.synthesize(
            text, out_path, speaker=speaker, emotion=emotion
        )
    except RuntimeError as exc:
        return {"error": str(exc)}
    return {"audio": str(out_path), "speaker": speaker, "emotion": emotion, "mos": mos}


@app.get("/healthz")  # type: ignore[misc]
async def healthz() -> dict[str, str]:
    """Basic liveness endpoint."""
    return {"status": "ok"}


__all__ = [
    "app",
    "generate_video",
    "list_styles",
    "broadcast_avatar_update",
    "capture_voice",
    "synthesize_voice",
    "voice_cloner",
]
