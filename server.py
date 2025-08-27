"""Minimal FastAPI server exposing health and utility endpoints.

The application powers local development tools and provides a few routes used
in tests:

* ``/health`` returns a plain liveness status.
* ``/glm-command`` executes a limited shell command when authorized.
* ``/avatar-frame`` streams the current video frame for the operator console.
* ``/music`` generates short audio clips with optional feedback logging.

Authentication is handled by a lightweight OAuth2 bearer token system. Real
deployments would integrate with a dedicated identity provider and persistent
storage.
"""

from __future__ import annotations

import base64
import logging
import time
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, Optional, TypedDict
import uuid

import numpy as np
import yaml
from fastapi import Depends, FastAPI, HTTPException, Security, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from PIL import Image
from prometheus_fastapi_instrumentator import Instrumentator

try:  # pragma: no cover - optional dependency
    from prometheus_client import Histogram
except ImportError:  # pragma: no cover - optional dependency
    Histogram = None  # type: ignore[assignment]
from pydantic import BaseModel, Field

from agents.razar.lifecycle_bus import LifecycleBus
from crown_prompt_orchestrator import crown_prompt_orchestrator
from INANNA_AI.glm_integration import GLMIntegration
from memory.mental import record_task_flow

import corpus_memory_logging
import music_generation
import vector_memory
import video_stream
from connectors import webrtc_connector
from core import feedback_logging, video_engine
from crown_config import settings
from glm_shell import send_command

logger = logging.getLogger(__name__)

REQUEST_LATENCY = (
    Histogram(
        "http_request_duration_seconds",
        "HTTP request latency",
        ["path", "method"],
    )
    if Histogram is not None
    else None
)

_glm = GLMIntegration()

# Lifecycle bus configuration -------------------------------------------------
try:
    _BUS_URL = (
        yaml.safe_load(Path("razar_config.yaml").read_text())
        .get("messaging", {})
        .get("lifecycle_bus")
    )
except Exception:
    _BUS_URL = None

_LIFECYCLE_BUS: LifecycleBus | None = None
if _BUS_URL:
    try:  # pragma: no cover - optional redis dependency
        _LIFECYCLE_BUS = LifecycleBus(url=_BUS_URL)
    except Exception:
        _LIFECYCLE_BUS = None

# --- OAuth2 security configuration ---
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "avatar:read": "Access avatar frames",
        "music:write": "Generate music",
        "music:read": "Download generated music",
        "glm:exec": "Execute GLM shell commands",
    },
)


# Simple in-memory token store. Real deployments would integrate with an
# identity provider. The configured ``GLM_COMMAND_TOKEN`` is reused to create a
# single privileged token.
class TokenInfo(TypedDict):
    sub: str
    scopes: set[str]


_TOKENS: dict[str, TokenInfo] = {}
if settings.glm_command_token:
    _TOKENS[settings.glm_command_token] = {
        "sub": "system",
        "scopes": {"avatar:read", "music:write", "music:read", "glm:exec"},
    }


# In-memory user database mapping usernames to passwords and tokens
_USERS: dict[str, dict[str, str]] = {}
if settings.openwebui_username and settings.openwebui_password:
    _user_token = uuid.uuid4().hex
    _USERS[settings.openwebui_username] = {
        "password": settings.openwebui_password,
        "token": _user_token,
    }
    _TOKENS[_user_token] = {
        "sub": settings.openwebui_username,
        "scopes": {"avatar:read", "music:write", "music:read"},
    }


def get_current_user(
    security_scopes: SecurityScopes, token: str = Security(oauth2_scheme)
) -> TokenInfo:
    """Validate ``token`` and enforce ``security_scopes``.

    Tokens are looked up in the in-memory ``_TOKENS`` dictionary. A ``401``
    error is raised when the token is missing or unknown and a ``403`` error is
    raised when it lacks one of the requested scopes.
    """

    token_info = _TOKENS.get(token)
    if not token_info:
        logger.warning("Unauthorized token for scopes %s", security_scopes.scope_str)
        raise HTTPException(status_code=401, detail="Invalid token")

    required = set(security_scopes.scopes)
    if not required.issubset(token_info["scopes"]):
        logger.warning(
            "Forbidden: %s lacks %s", token_info.get("sub"), security_scopes.scope_str
        )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    logger.info(
        "Access granted for %s to %s", token_info.get("sub"), security_scopes.scope_str
    )
    return token_info




@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown tasks for the FastAPI app.

    The context manager yields control to FastAPI and, once the server begins
    shutting down, closes any open WebRTC or video streaming connections so the
    test harness and local development environment exit cleanly.
    """
    yield
    await video_stream.close_peers()
    await webrtc_connector.close_peers()


app = FastAPI(lifespan=lifespan)
app.include_router(video_stream.router)
app.include_router(webrtc_connector.router)

Instrumentator().instrument(app).expose(app)


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict[str, str]:
    """Validate user credentials and return an access token."""
    user = _USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        logger.warning("Invalid login for %s", form_data.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": user["token"], "token_type": "bearer"}


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    if REQUEST_LATENCY is not None:
        REQUEST_LATENCY.labels(request.url.path, request.method).observe(duration)
    logger.info(
        "request completed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "duration": duration,
        },
    )
    return response


_avatar_stream: Optional[Iterator[np.ndarray]] = None

_ALLOWED_PREFIXES = {
    "ls",
    "cat",
    "rg",
    "git",
    "black",
    "isort",
    "pre-commit",
}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "alive"}


@app.get("/ready")
def readiness_check() -> dict[str, str]:
    """Return service readiness status."""
    return {"status": "ready"}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]


@app.post("/openwebui-chat")
def openwebui_chat(
    req: ChatCompletionRequest,
    current_user: dict = Security(get_current_user),
) -> dict[str, Any]:
    """Return an OpenAI-style chat completion."""
    if _LIFECYCLE_BUS is not None:
        _LIFECYCLE_BUS.publish_status("openwebui_session", "start")
    try:
        user_content = ""
        for msg in req.messages:
            if msg.role == "user":
                user_content = msg.content
        result = crown_prompt_orchestrator(user_content, _glm)
        corpus_memory_logging.log_interaction(
            user_content,
            {
                "intent": "openwebui_chat",
                "model": result.get("model", req.model or "unknown"),
            },
            {"response": result.get("text", "")},
            "success",
        )
        record_task_flow(
            "openwebui_chat",
            {
                "user": user_content,
                "response": result.get("text", ""),
                "model": result.get("model", req.model or "unknown"),
            },
        )
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": result.get("model", req.model or "unknown"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.get("text", ""),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }
    finally:
        if _LIFECYCLE_BUS is not None:
            _LIFECYCLE_BUS.publish_status("openwebui_session", "end")


class ShellCommand(BaseModel):
    """Payload for ``/glm-command``."""

    command: str = Field(min_length=1)


if settings.glm_command_token:

    @app.post("/glm-command")
    def glm_command(
        cmd: ShellCommand,
        current_user: dict = Security(get_current_user, scopes=["glm:exec"]),
    ) -> dict[str, str | bool]:
        """Execute ``cmd.command`` via the GLM shell and return the result."""
        prefix = cmd.command.split()[0]
        if prefix not in _ALLOWED_PREFIXES:
            vector_memory.add_vector(
                cmd.command,
                {"intent": "glm_command", "outcome": "rejected"},
            )
            logger.warning(
                "Rejected command %s by %s",
                cmd.command,
                current_user.get("sub"),
            )
            raise HTTPException(status_code=400, detail="command not allowed")
        try:
            result = send_command(cmd.command)
        except Exception as exc:  # pragma: no cover - GLM failure
            vector_memory.add_vector(
                cmd.command,
                {
                    "intent": "glm_command",
                    "outcome": "error",
                    "error": str(exc),
                },
            )
            logger.exception("GLM command failed")
            raise HTTPException(status_code=500, detail="command failed") from exc
        vector_memory.add_vector(
            cmd.command, {"intent": "glm_command", "outcome": "success"}
        )
        logger.info(
            "Executed GLM command %s for %s", cmd.command, current_user.get("sub")
        )
        return {"ok": True, "result": result}

else:
    logger.warning("GLM_COMMAND_TOKEN not set; /glm-command endpoint disabled")


@app.get("/avatar-frame")
def avatar_frame(
    current_user: dict = Security(get_current_user, scopes=["avatar:read"])
) -> JSONResponse:
    """Return the next avatar frame as a base64 encoded PNG."""
    global _avatar_stream
    if _avatar_stream is None:
        _avatar_stream = video_engine.start_stream()
    frame = next(_avatar_stream)
    img = Image.fromarray(frame.astype(np.uint8))
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    logger.info("Avatar frame served for %s", current_user.get("sub"))
    return JSONResponse({"frame": b64})


class MusicRequest(BaseModel):
    """Payload for ``/music`` generation."""

    prompt: str = Field(min_length=1)
    model: str | None = None
    feedback: str | None = None
    rating: float | None = Field(default=None, ge=0.0, le=1.0)


@app.post("/music")
def generate_music(
    req: MusicRequest,
    current_user: dict = Security(get_current_user, scopes=["music:write"]),
) -> dict[str, str]:
    """Generate music from ``req.prompt`` and return a download path."""
    logger.info("Music generation requested by %s", current_user.get("sub"))
    try:
        path = music_generation.generate_from_text(req.prompt, req.model or "musicgen")
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
def get_music(
    filename: str,
    current_user: dict = Security(get_current_user, scopes=["music:read"]),
) -> FileResponse:
    """Return generated music file ``filename``."""
    path = music_generation.OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    logger.info("Music file %s served for %s", filename, current_user.get("sub"))
    return FileResponse(path)
