from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import numpy as np
from fastapi.testclient import TestClient
from fastapi import APIRouter

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

async def _close_peers(*a, **k) -> None:
    pass

video_stream_stub.close_peers = _close_peers
video_stream_stub.start_stream = (
    lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
)
sys.modules.setdefault("video_stream", video_stream_stub)

connectors_mod = ModuleType("connectors")
webrtc_stub = ModuleType("webrtc_connector")
webrtc_stub.router = APIRouter()
webrtc_stub.start_call = lambda *a, **k: None
async def _wc_close(*a, **k) -> None:
    pass

webrtc_stub.close_peers = _wc_close
connectors_mod.webrtc_connector = webrtc_stub
sys.modules.setdefault("connectors", connectors_mod)
sys.modules.setdefault("connectors.webrtc_connector", webrtc_stub)

import server


def test_health_and_ready():
    with TestClient(server.app) as client:
        health = client.get("/health")
        ready = client.get("/ready")
    assert health.status_code == 200
    assert health.json() == {"status": "alive"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_glm_command_authorized(monkeypatch):
    monkeypatch.setattr(server, "send_command", lambda c: f"ran {c}")
    monkeypatch.setattr(server, "GLM_COMMAND_TOKEN", "token")
    with TestClient(server.app) as client:
        resp = client.post(
            "/glm-command",
            json={"command": "ls"},
            headers={"Authorization": "token"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"result": "ran ls"}


def test_glm_command_requires_authorization(monkeypatch):
    monkeypatch.setattr(server, "send_command", lambda c: "out")
    monkeypatch.setattr(server, "GLM_COMMAND_TOKEN", "token")
    with TestClient(server.app) as client:
        missing = client.post("/glm-command", json={"command": "ls"})
        wrong = client.post(
            "/glm-command",
            json={"command": "ls"},
            headers={"Authorization": "bad"},
        )
    assert missing.status_code == 401
    assert wrong.status_code == 401
