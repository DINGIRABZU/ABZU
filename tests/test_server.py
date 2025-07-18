import sys
from pathlib import Path
import asyncio

import httpx
import numpy as np
from fastapi.testclient import TestClient
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))
sys.modules.setdefault("core", ModuleType("core"))
video_engine_stub = ModuleType("video_engine")
video_engine_stub.start_stream = lambda: iter([np.zeros((1,1,3), dtype=np.uint8)])
sys.modules.setdefault("core.video_engine", video_engine_stub)
from fastapi import APIRouter
video_stream_stub = ModuleType("video_stream")
video_stream_stub.router = APIRouter()
video_stream_stub.close_peers = lambda *a, **k: None
video_stream_stub.start_stream = lambda: iter([np.zeros((1,1,3), dtype=np.uint8)])
sys.modules.setdefault("video_stream", video_stream_stub)
connectors_mod = ModuleType("connectors")
webrtc_stub = ModuleType("webrtc_connector")
webrtc_stub.router = APIRouter()
webrtc_stub.start_call = lambda *a, **k: None
webrtc_stub.close_peers = lambda *a, **k: None
connectors_mod.webrtc_connector = webrtc_stub
sys.modules.setdefault("connectors", connectors_mod)
sys.modules.setdefault("connectors.webrtc_connector", webrtc_stub)
init_crown_stub = ModuleType("init_crown_agent")
init_crown_stub.initialize_crown = lambda *a, **k: None
sys.modules.setdefault("init_crown_agent", init_crown_stub)
inanna_mod = ModuleType("INANNA_AI.glm_integration")
inanna_mod.GLMIntegration = lambda *a, **k: None
sys.modules.setdefault("INANNA_AI.glm_integration", inanna_mod)

import server


def test_health_and_ready_return_200():
    """Endpoints should respond with HTTP 200 when app is running."""

    async def run_requests() -> tuple[int, int]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            health = await client.get("/health")
            ready = await client.get("/ready")
        return health.status_code, ready.status_code

    status_health, status_ready = asyncio.run(run_requests())
    assert status_health == 200
    assert status_ready == 200


def test_glm_command_endpoint(monkeypatch):
    """POST /glm-command should return GLM output when authorized."""

    async def run_request() -> tuple[int, dict[str, str]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/glm-command",
                json={"command": "ls"},
                headers={"Authorization": "token"},
            )
        return resp.status_code, resp.json()

    monkeypatch.setattr(server, "send_command", lambda cmd: f"ran {cmd}")
    monkeypatch.setattr(server, "GLM_COMMAND_TOKEN", "token")
    status, data = asyncio.run(run_request())
    assert status == 200
    assert data == {"result": "ran ls"}


def test_glm_command_requires_authorization(monkeypatch):
    """/glm-command should return 401 when token is missing or wrong."""

    async def run_request(headers) -> int:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/glm-command", json={"command": "ls"}, headers=headers
            )
        return resp.status_code

    monkeypatch.setattr(server, "send_command", lambda cmd: "ran")
    monkeypatch.setattr(server, "GLM_COMMAND_TOKEN", "token")
    status_missing = asyncio.run(run_request({}))
    status_wrong = asyncio.run(run_request({"Authorization": "bad"}))
    assert status_missing == 401
    assert status_wrong == 401


def test_avatar_frame_endpoint(monkeypatch):
    """GET /avatar-frame should return a base64 encoded image."""

    async def run_request() -> tuple[int, dict[str, str]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/avatar-frame")
        return resp.status_code, resp.json()

    frames = iter([np.zeros((1, 1, 3), dtype=np.uint8)])
    monkeypatch.setattr(server, "_avatar_stream", None)
    monkeypatch.setattr(server.video_engine, "start_stream", lambda: frames)

    status, data = asyncio.run(run_request())
    assert status == 200
    assert isinstance(data.get("frame"), str) and len(data["frame"]) > 0
