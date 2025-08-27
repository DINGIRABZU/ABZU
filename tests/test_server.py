"""Tests for server."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))
sys.modules.setdefault("core", ModuleType("core"))
video_engine_stub = ModuleType("video_engine")
video_engine_stub.start_stream = lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
feedback_logging_stub = ModuleType("feedback_logging")
feedback_logging_stub.append_feedback = lambda *a, **k: None
core_mod = sys.modules["core"]
core_mod.video_engine = video_engine_stub
core_mod.feedback_logging = feedback_logging_stub
sys.modules.setdefault("core.video_engine", video_engine_stub)
sys.modules.setdefault("core.feedback_logging", feedback_logging_stub)
# Stub optional dependencies used by memory.mental
core_utils_stub = ModuleType("core.utils")
optional_deps_stub = ModuleType("optional_deps")
optional_deps_stub.lazy_import = lambda name: SimpleNamespace(__stub__=True)
core_utils_stub.optional_deps = optional_deps_stub
sys.modules.setdefault("core.utils", core_utils_stub)
sys.modules.setdefault("core.utils.optional_deps", optional_deps_stub)
from fastapi import APIRouter

video_stream_stub = ModuleType("video_stream")
video_stream_stub.router = APIRouter()


async def _close_vs(*a, **k) -> None:
    pass


video_stream_stub.close_peers = _close_vs
video_stream_stub.start_stream = lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
sys.modules.setdefault("video_stream", video_stream_stub)
connectors_mod = ModuleType("connectors")
webrtc_stub = ModuleType("webrtc_connector")
webrtc_stub.router = APIRouter()
webrtc_stub.start_call = lambda *a, **k: None


async def _close_wc(*a, **k) -> None:
    pass


webrtc_stub.close_peers = _close_wc
connectors_mod.webrtc_connector = webrtc_stub
sys.modules.setdefault("connectors", connectors_mod)
sys.modules.setdefault("connectors.webrtc_connector", webrtc_stub)
init_crown_stub = ModuleType("init_crown_agent")
init_crown_stub.initialize_crown = lambda *a, **k: None
sys.modules.setdefault("init_crown_agent", init_crown_stub)
inanna_mod = ModuleType("INANNA_AI.glm_integration")
inanna_mod.GLMIntegration = lambda *a, **k: None
sys.modules.setdefault("INANNA_AI.glm_integration", inanna_mod)

corpus_memory_logging_stub = ModuleType("corpus_memory_logging")
corpus_memory_logging_stub.log_interaction = lambda *a, **k: None
corpus_memory_logging_stub.load_interactions = lambda *a, **k: []
corpus_memory_logging_stub.log_ritual_result = lambda *a, **k: None
sys.modules.setdefault("corpus_memory_logging", corpus_memory_logging_stub)

music_generation_stub = ModuleType("music_generation")
music_generation_stub.generate_from_text = lambda *a, **k: Path("song.wav")
music_generation_stub.OUTPUT_DIR = Path(".")
sys.modules.setdefault("music_generation", music_generation_stub)

crown_mod = ModuleType("crown_prompt_orchestrator")
crown_mod.crown_prompt_orchestrator = lambda msg, glm: {
    "text": "stubbed",
    "model": "stub",
}
sys.modules.setdefault("crown_prompt_orchestrator", crown_mod)

from crown_config import settings

settings.glm_command_token = "token"
import server
server.record_task_flow = lambda *a, **k: None


def test_health_and_ready_return_200():
    """Endpoints should respond with HTTP 200 and expected payload."""

    async def run_requests() -> tuple[tuple[int, dict[str, str]], int]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            health = await client.get("/health")
            ready = await client.get("/ready")
        return (health.status_code, health.json()), ready.status_code

    (status_health, body_health), status_ready = asyncio.run(run_requests())
    assert status_health == 200
    assert body_health == {"status": "alive"}
    assert status_ready == 200


def test_glm_command_endpoint(monkeypatch):
    """POST /glm-command should return GLM output when authorized."""

    async def run_request() -> tuple[int, dict[str, str | bool]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/glm-command",
                json={"command": "ls"},
                headers={"Authorization": "Bearer token"},
            )
        return resp.status_code, resp.json()

    monkeypatch.setattr(server, "send_command", lambda cmd: f"ran {cmd}")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda t, m: None)
    status, data = asyncio.run(run_request())
    assert status == 200
    assert data == {"ok": True, "result": "ran ls"}


def test_glm_command_requires_authorization(monkeypatch):
    """/glm-command should return 401 when token is missing or wrong."""

    async def run_request(headers) -> int:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/glm-command", json={"command": "ls"}, headers=headers
            )
        return resp.status_code

    monkeypatch.setattr(server, "send_command", lambda cmd: "ran")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda t, m: None)
    status_missing = asyncio.run(run_request({}))
    status_wrong = asyncio.run(run_request({"Authorization": "Bearer bad"}))
    assert status_missing == 401
    assert status_wrong == 401


def test_avatar_frame_endpoint(monkeypatch):
    """GET /avatar-frame should return a base64 encoded image."""

    async def run_request() -> tuple[int, dict[str, str]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/avatar-frame", headers={"Authorization": "Bearer token"}
            )
        return resp.status_code, resp.json()

    frames = iter([np.zeros((1, 1, 3), dtype=np.uint8)])
    monkeypatch.setattr(server, "_avatar_stream", None)
    monkeypatch.setattr(server.video_engine, "start_stream", lambda: frames)

    status, data = asyncio.run(run_request())
    assert status == 200
    assert isinstance(data.get("frame"), str) and len(data["frame"]) > 0


def test_music_endpoint_success(monkeypatch, tmp_path):
    """POST /music should return path when generation succeeds."""

    song = tmp_path / "song.wav"
    song.write_bytes(b"wav")

    monkeypatch.setattr(
        server.music_generation, "generate_from_text", lambda p, m: song
    )
    monkeypatch.setattr(server.music_generation, "OUTPUT_DIR", tmp_path)

    async def run_request():
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/music",
                json={"prompt": "melody"},
                headers={"Authorization": "Bearer token"},
            )
        return resp.status_code, resp.json()

    status, data = asyncio.run(run_request())
    assert status == 200
    assert data == {"wav": "/music/song.wav"}


def test_music_endpoint_failure(monkeypatch):
    """POST /music should return 500 when generation fails."""

    def boom(*a, **k):
        raise RuntimeError("fail")

    monkeypatch.setattr(server.music_generation, "generate_from_text", boom)

    async def run_request():
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/music",
                json={"prompt": "melody"},
                headers={"Authorization": "Bearer token"},
            )
        return resp.status_code

    status = asyncio.run(run_request())
    assert status == 500


def test_openwebui_chat_endpoint():
    """POST /openwebui-chat should return an OpenAI-style response."""

    async def run_request() -> tuple[int, dict[str, object]]:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/openwebui-chat",
                json={"model": "stub", "messages": [{"role": "user", "content": "hi"}]},
                headers={"Authorization": "Bearer token"},
            )
        return resp.status_code, resp.json()

    status, data = asyncio.run(run_request())
    assert status == 200
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "stubbed"


def test_openwebui_chat_requires_authorization():
    """/openwebui-chat should return 401 without a valid token."""

    async def run_request(headers) -> int:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.post(
                "/openwebui-chat",
                json={"model": "stub", "messages": [{"role": "user", "content": "hi"}]},
                headers=headers,
            )
        return resp.status_code

    status = asyncio.run(run_request({}))
    assert status == 401


def test_get_music_not_found():
    """GET /music/<file> should return 404 when missing."""

    async def run_request() -> int:
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp = await client.get(
                "/music/missing.wav", headers={"Authorization": "Bearer token"}
            )
        return resp.status_code

    status = asyncio.run(run_request())
    assert status == 404


def test_import_src_package():
    """Import modules under ``src`` to increase coverage."""

    import importlib

    mod = importlib.import_module("src")
    contracts = importlib.import_module("src.core.contracts")
    assert mod.__name__ == "src" and contracts.__name__ == "src.core.contracts"
