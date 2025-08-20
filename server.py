"""Simple FastAPI application for health checks."""
from __future__ import annotations

import logging
import secrets
import base64
from io import BytesIO
from typing import Iterator, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from PIL import Image
import numpy as np

from core import video_engine
import video_stream
from connectors import webrtc_connector
from glm_shell import send_command
from config import settings
import music_generation
import corpus_memory_logging
import feedback_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await video_stream.close_peers()
    await webrtc_connector.close_peers()


app = FastAPI(lifespan=lifespan)
app.include_router(video_stream.router)
app.include_router(webrtc_connector.router)

_avatar_stream: Optional[Iterator[np.ndarray]] = None


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "alive"}


@app.get("/ready")
def readiness_check() -> dict[str, str]:
    """Return service readiness status."""
    return {"status": "ready"}


class ShellCommand(BaseModel):
    """Payload for ``/glm-command``."""

    command: str


if settings.glm_command_token:
    @app.post("/glm-command")
    def glm_command(cmd: ShellCommand, request: Request) -> dict[str, str]:
        """Execute ``cmd.command`` via the GLM shell and return the result."""
        auth_header = request.headers.get("Authorization") or ""
        if not secrets.compare_digest(auth_header, settings.glm_command_token):
            raise HTTPException(status_code=401, detail="Unauthorized")
        result = send_command(cmd.command)
        return {"result": result}
else:
    logger.warning("GLM_COMMAND_TOKEN not set; /glm-command endpoint disabled")


@app.get("/avatar-frame")
def avatar_frame() -> JSONResponse:
    """Return the next avatar frame as a base64 encoded PNG."""
    global _avatar_stream
    if _avatar_stream is None:
        _avatar_stream = video_engine.start_stream()
    frame = next(_avatar_stream)
    img = Image.fromarray(frame.astype(np.uint8))
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return JSONResponse({"frame": b64})


class MusicRequest(BaseModel):
    """Payload for ``/music`` generation."""

    prompt: str
    model: str | None = None
    feedback: str | None = None
    rating: float | None = None


@app.post("/music")
def generate_music(req: MusicRequest) -> dict[str, str]:
    """Generate music from ``req.prompt`` and return a download path."""
    try:
        path = music_generation.generate_from_text(
            req.prompt, req.model or "musicgen"
        )
        corpus_memory_logging.log_interaction(
            req.prompt,
            {"intent": "music_generation", "model": req.model or "musicgen"},
            {"path": str(path)},
            "success",
            feedback=req.feedback,
            rating=req.rating,
        )
        if req.feedback or req.rating is not None:
            feedback_logging.append_feedback(
                {
                    "intent": "music_generation",
                    "action": "generate",
                    "prompt": req.prompt,
                    "feedback": req.feedback,
                    "rating": req.rating,
                    "success": True,
                }
            )
        return {"wav": f"/music/{path.name}"}
    except Exception as exc:
        corpus_memory_logging.log_interaction(
            req.prompt,
            {"intent": "music_generation", "model": req.model or "musicgen"},
            {"error": str(exc)},
            "error",
            feedback=req.feedback,
            rating=req.rating,
        )
        if req.feedback or req.rating is not None:
            feedback_logging.append_feedback(
                {
                    "intent": "music_generation",
                    "action": "generate",
                    "prompt": req.prompt,
                    "feedback": req.feedback,
                    "rating": req.rating,
                    "success": False,
                }
            )
        raise HTTPException(status_code=500, detail="music generation failed")


@app.get("/music/{filename}")
def get_music(filename: str) -> FileResponse:
    """Return generated music file ``filename``."""
    path = music_generation.OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path)
