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

- **Endpoints:** ``/health``, ``POST /glm-command``, ``/avatar-frame``, ``/music``
- **Auth:** Bearer token
- **Linked services:** Open WebUI console
"""

from __future__ import annotations

__version__ = "0.1.1"

import base64
import json
import logging
import time
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    Optional,
    TypedDict,
)
import uuid

import numpy as np
import yaml  # type: ignore[import-untyped]
from fastapi import Depends, FastAPI, HTTPException, Security, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from PIL import Image
from prometheus_fastapi_instrumentator import Instrumentator

try:  # pragma: no cover - optional dependency
    from prometheus_client import Histogram, Gauge, REGISTRY
except ImportError:  # pragma: no cover - optional dependency
    Histogram = Gauge = REGISTRY = None  # type: ignore[assignment]
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
from communication.floor_channel_socket import socket_app
from nlq_api import router as nlq_router
from operator_api import router as operator_router
from agents.sidekick_helper import router as sidekick_router

logger = logging.getLogger(__name__)

START_TIME = time.perf_counter()

if Gauge is not None and REGISTRY is not None:
    if "service_boot_duration_seconds" in REGISTRY._names_to_collectors:
        BOOT_DURATION_GAUGE = REGISTRY._names_to_collectors[
            "service_boot_duration_seconds"
        ]  # type: ignore[assignment]
    else:
        BOOT_DURATION_GAUGE = Gauge(
            "service_boot_duration_seconds",
            "Duration of service startup in seconds",
            ["service"],
        )
else:
    BOOT_DURATION_GAUGE = None

REQUEST_LATENCY = (
    Histogram(
        "http_request_duration_seconds",
        "HTTP request latency",
        ["path", "method"],
    )
    if Histogram is not None
    else None
)

INDEX_ENTRY_GAUGE = (
    Gauge(
        "component_index_entries",
        "Number of components listed in component_index.json",
    )
    if Gauge is not None
    else None
)

AVERAGE_COVERAGE_GAUGE = (
    Gauge(
        "component_index_average_coverage",
        "Average coverage percentage across components",
    )
    if Gauge is not None
    else None
)


def _refresh_component_index_metrics() -> None:
    """Load component index metrics into Prometheus gauges."""
    if INDEX_ENTRY_GAUGE is None or AVERAGE_COVERAGE_GAUGE is None:
        return
    try:
        data = json.loads(Path("component_index.json").read_text(encoding="utf-8"))
        components = data.get("components", [])
        INDEX_ENTRY_GAUGE.set(len(components))  # type: ignore[call-arg]
        coverages = [c.get("metrics", {}).get("coverage", 0.0) for c in components]
        if coverages:
            AVERAGE_COVERAGE_GAUGE.set(sum(coverages) / len(coverages))  # type: ignore[call-arg]
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to refresh component index metrics: %s", exc)


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
    """OAuth token details used for authorization."""

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


# Rendering mode per agent ----------------------------------------------------
_AVATAR_MODES: dict[str, str] = {}


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

    The context manager records boot duration before yielding control to
    FastAPI and, once the server begins shutting down, closes any open WebRTC
    or video streaming connections so the test harness and local development
    environment exit cleanly.
    """
    if BOOT_DURATION_GAUGE is not None:
        BOOT_DURATION_GAUGE.labels(service="core").set(time.perf_counter() - START_TIME)
    try:
        _glm.health_check()
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error("GLM health check failed: %s", exc)
        raise SystemExit("GLM endpoint unavailable") from exc
    yield
    await video_stream.close_peers()
    await webrtc_connector.close_peers()


app = FastAPI(lifespan=lifespan)
app.include_router(video_stream.router)
app.include_router(webrtc_connector.router)
app.include_router(nlq_router)
app.include_router(operator_router)
app.include_router(sidekick_router)

Instrumentator().instrument(app).expose(app)
_refresh_component_index_metrics()
app.mount("/ws", socket_app)


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict[str, str]:
    """Validate user credentials and return an access token."""
    user = _USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        logger.warning("Invalid login for %s", form_data.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": user["token"], "token_type": "bearer"}


@app.middleware("http")
async def log_request_time(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Record request latency and export it to Prometheus."""
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


@app.get("/healthz")
def healthz_check() -> dict[str, str]:
    """Alias of ``/health`` for Kubernetes probes."""
    return health_check()


@app.get("/ready")
def readiness_check() -> dict[str, str]:
    """Return service readiness status."""
    return {"status": "ready"}


class ChatMessage(BaseModel):
    """Chat message exchanged with the OpenWebUI interface."""

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """Payload for chat completion requests."""

    model: str | None = None
    messages: list[ChatMessage]


def nazarick_chat(channel: str, text: str) -> dict[str, Any]:
    """Return response from a Nazarick agent for ``text`` sent to ``channel``.

    The default implementation simply delegates to ``crown_prompt_orchestrator``
    so tests can patch this hook to verify channel routing without relying on
    external services.
    """

    return crown_prompt_orchestrator(text, _glm)


@app.post("/openwebui-chat")
def openwebui_chat(
    req: ChatCompletionRequest,
    channel: str | None = None,
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
        if channel:
            result = nazarick_chat(channel, user_content)
        else:
            result = crown_prompt_orchestrator(user_content, _glm)
        corpus_memory_logging.log_interaction(
            user_content,
            {
                "intent": "openwebui_chat",
                "channel": channel or "crown",
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
                "channel": channel or "crown",
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


@app.post("/agents/{agent_id}/avatar-mode")
def set_avatar_mode(
    agent_id: str,
    data: dict[str, str],
    current_user: dict = Security(get_current_user, scopes=["avatar:read"]),
) -> dict[str, str]:
    """Set the rendering mode (``2d`` or ``3d``) for ``agent_id``."""

    mode = data.get("mode", "")
    if mode not in {"2d", "3d"}:
        raise HTTPException(status_code=400, detail="mode must be '2d' or '3d'")
    _AVATAR_MODES[agent_id] = mode
    logger.info("Set avatar mode for %s to %s", agent_id, mode)
    return {"agent": agent_id, "mode": mode}


@app.get("/agents/{agent_id}/avatar-mode")
def get_avatar_mode(
    agent_id: str,
    current_user: dict = Security(get_current_user, scopes=["avatar:read"]),
) -> dict[str, str]:
    """Return the rendering mode for ``agent_id``."""

    mode = _AVATAR_MODES.get(agent_id, "2d")
    return {"agent": agent_id, "mode": mode}


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
