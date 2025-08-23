"""Tests for api endpoints."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _app(tmp_path, monkeypatch):
    from api import server

    (tmp_path / "demo.yaml").write_text("processor: demo")
    monkeypatch.setattr(server.style_library, "STYLES_DIR", tmp_path)
    server._connections.clear()
    return server.app


def test_generate_video_and_styles(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with TestClient(app) as client:
        resp = client.post("/generate_video", json={"prompt": "hi"})
        assert resp.status_code == 200
        assert resp.json() == {"status": "queued", "prompt": "hi"}

        styles = client.get("/styles")
        assert styles.status_code == 200
        assert styles.json() == {"styles": ["demo"]}


def test_stream_avatar(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    with TestClient(app).websocket_connect("/stream_avatar") as ws:
        ws.send_text("frame1")
        data = ws.receive_text()
        assert data == "frame1"
