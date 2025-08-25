"""Tests for FastAPI server endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

np = pytest.importorskip("numpy")
pytest.importorskip("fastapi")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))

# --- minimal stubs required to import server -------------------------------
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


async def _vs_close(*a, **k) -> None:
    return None


video_stream_stub.close_peers = _vs_close
sys.modules["video_stream"] = video_stream_stub

connectors_mod = ModuleType("connectors")
webrtc_stub = ModuleType("webrtc_connector")
webrtc_stub.router = APIRouter()


async def _wc_close(*a, **k) -> None:
    return None


webrtc_stub.close_peers = _wc_close
connectors_mod.webrtc_connector = webrtc_stub
sys.modules["connectors"] = connectors_mod
sys.modules["connectors.webrtc_connector"] = webrtc_stub

from crown_config import settings

settings.glm_command_token = "token"
import server


def test_health_check():
    """`/health` returns a simple alive status."""
    with TestClient(server.app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}


def test_glm_command_exec(monkeypatch):
    """Authorized `/glm-command` executes whitelisted shell commands."""
    monkeypatch.setattr(server, "send_command", lambda c: "out")
    monkeypatch.setattr(server.vector_memory, "add_vector", lambda *a, **k: None)
    with TestClient(server.app) as client:
        resp = client.post(
            "/glm-command",
            json={"command": "ls"},
            headers={"Authorization": "Bearer token"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "result": "out"}


def test_glm_command_requires_auth():
    """Missing token on `/glm-command` should return 401."""
    with TestClient(server.app) as client:
        resp = client.post("/glm-command", json={"command": "ls"})
    assert resp.status_code == 401
