from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import numpy as np
from fastapi.testclient import TestClient
from fastapi import APIRouter
import importlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))
sys.modules.setdefault("core", ModuleType("core"))

video_engine_stub = ModuleType("video_engine")
video_engine_stub.start_stream = lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
sys.modules.setdefault("core.video_engine", video_engine_stub)

video_stream_stub = ModuleType("video_stream")
video_stream_stub.router = APIRouter()

closed_vs: list[str] = []

async def _close_peers(*a, **k) -> None:
    closed_vs.append("v")

video_stream_stub.close_peers = _close_peers
video_stream_stub.start_stream = (
    lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
)
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
import importlib

def _load_server():
    import server
    return importlib.reload(server)


def test_health_and_ready():
    server = _load_server()
    with TestClient(server.app) as client:
        health = client.get("/health")
        ready = client.get("/ready")
    assert health.status_code == 200
    assert health.json() == {"status": "alive"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_glm_command_authorized(monkeypatch):
    server = _load_server()
    monkeypatch.setattr(server, "send_command", lambda c: f"ran {c}")
    with TestClient(server.app) as client:
        resp = client.post(
            "/glm-command",
            json={"command": "ls"},
            headers={"Authorization": "token"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"result": "ran ls"}


def test_glm_command_requires_authorization(monkeypatch):
    server = _load_server()
    monkeypatch.setattr(server, "send_command", lambda c: "out")
    with TestClient(server.app) as client:
        missing = client.post("/glm-command", json={"command": "ls"})
        wrong = client.post(
            "/glm-command",
            json={"command": "ls"},
            headers={"Authorization": "bad"},
        )
    assert missing.status_code == 401
    assert wrong.status_code == 401


def test_shutdown_closes_streams():
    server = _load_server()
    closed_vs.clear()
    closed_wc.clear()
    with TestClient(server.app):
        pass
    assert "v" in closed_vs and "w" in closed_wc
