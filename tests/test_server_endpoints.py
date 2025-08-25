"""Tests for server endpoints."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("fastapi")

from fastapi import APIRouter
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))

video_engine_stub = ModuleType("video_engine")
video_engine_stub.start_stream = lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])

feedback_logging_stub = ModuleType("feedback_logging")

core_stub = ModuleType("core")
core_stub.video_engine = video_engine_stub
core_stub.feedback_logging = feedback_logging_stub

sys.modules["core"] = core_stub
sys.modules["core.video_engine"] = video_engine_stub
sys.modules["core.feedback_logging"] = feedback_logging_stub

vector_memory_stub = ModuleType("vector_memory")
vector_memory_stub.add_vector = lambda *a, **k: None
sys.modules["vector_memory"] = vector_memory_stub

music_generation_stub = ModuleType("music_generation")
music_generation_stub.generate_from_text = lambda *a, **k: Path("dummy.wav")
sys.modules["music_generation"] = music_generation_stub

video_stream_stub = ModuleType("video_stream")
video_stream_stub.router = APIRouter()

closed_vs: list[str] = []


async def _close_peers(*a, **k) -> None:
    closed_vs.append("v")


video_stream_stub.close_peers = _close_peers
video_stream_stub.start_stream = lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
sys.modules["video_stream"] = video_stream_stub

connectors_mod = ModuleType("connectors")
webrtc_stub = ModuleType("webrtc_connector")
webrtc_stub.router = APIRouter()
webrtc_stub.start_call = lambda *a, **k: None
closed_wc: list[str] = []


async def _wc_close(*a, **k) -> None:
    closed_wc.append("w")


webrtc_stub.close_peers = _wc_close
connectors_mod.webrtc_connector = webrtc_stub
sys.modules["connectors"] = connectors_mod
sys.modules["connectors.webrtc_connector"] = webrtc_stub

init_crown_stub = ModuleType("init_crown_agent")
init_crown_stub.initialize_crown = lambda *a, **k: None
sys.modules.setdefault("init_crown_agent", init_crown_stub)

inanna_mod = ModuleType("INANNA_AI.glm_integration")
inanna_mod.GLMIntegration = lambda *a, **k: None
sys.modules.setdefault("INANNA_AI.glm_integration", inanna_mod)

from crown_config import settings

settings.glm_command_token = "token"


def _load_server():
    import server

    return importlib.reload(server)


def test_health_check():
    server = _load_server()
    with TestClient(server.app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}


def test_glm_command_authorized(monkeypatch):
    server = _load_server()
    monkeypatch.setattr(server, "send_command", lambda c: f"ran {c}")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda t, m: None)
    with TestClient(server.app) as client:
        resp = client.post(
            "/glm-command",
            json={"command": "ls"},
            headers={"Authorization": "Bearer token"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "result": "ran ls"}


def test_glm_command_requires_authorization(monkeypatch):
    server = _load_server()
    monkeypatch.setattr(server, "send_command", lambda c: "out")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda t, m: None)
    with TestClient(server.app) as client:
        missing = client.post("/glm-command", json={"command": "ls"})
        wrong = client.post(
            "/glm-command",
            json={"command": "ls"},
            headers={"Authorization": "Bearer bad"},
        )
    assert missing.status_code == 401
    assert wrong.status_code == 401


def test_shutdown_closes_streams():
    server = _load_server()
    closed_vs.clear()
    closed_wc.clear()
    with TestClient(server.app) as client:
        # trigger startup with a simple request
        resp = client.get("/health")
        assert resp.status_code == 200
    assert "v" in closed_vs and "w" in closed_wc
