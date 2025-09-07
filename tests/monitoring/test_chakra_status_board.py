from __future__ import annotations

import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from monitoring.chakra_heartbeat import ChakraHeartbeat
from monitoring import chakra_status_board as board
from agents.razar import state_validator


def _create_app(hb: ChakraHeartbeat) -> FastAPI:
    app = FastAPI()
    board.heartbeat = hb
    app.include_router(board.router)
    return app


def test_status_board_reports_heartbeats_and_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hb = ChakraHeartbeat(window=10.0, memory=None)
    hb.beat("root", timestamp=0.0)
    hb.beat("crown", timestamp=0.0)

    fake_time = types.SimpleNamespace(time=lambda: 1.0)
    monkeypatch.setattr(board, "time", fake_time)

    app = _create_app(hb)
    with TestClient(app) as client:
        data = client.get("/chakra/status").json()
        assert data["status"] == "Great Spiral"
        assert data["heartbeats"]["root"] == pytest.approx(1.0)
        assert data["heartbeats"]["crown"] == pytest.approx(1.0)
        assert data["versions"]["state_validator"] == state_validator.__version__
        metrics = client.get("/metrics").text
    assert 'chakra_pulse_hz{chakra="root"} 1.0' in metrics
    expected = (
        'component_version_info{component="state_validator",version="'
        + state_validator.__version__
        + '"} 1.0'
    )
    assert expected in metrics
