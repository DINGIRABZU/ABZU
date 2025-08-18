"""Simple FastAPI application for health checks."""
from __future__ import annotations

import logging
import secrets
import base64
from io import BytesIO
from typing import Iterator, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
import numpy as np

from core import video_engine
import video_stream
from connectors import webrtc_connector
from glm_shell import send_command
from config import settings

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(video_stream.router)
app.include_router(webrtc_connector.router)


@app.on_event("shutdown")
async def _close_peers() -> None:
    await video_stream.close_peers()
    await webrtc_connector.close_peers()

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
