"""Tests for chakracon API endpoints."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

import chakracon.api as api


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api.router)
    return app


def test_metrics_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    app = create_app()

    def fake_get(
        url: str, params: dict[str, str] | None = None, timeout: int = 5
    ) -> object:
        assert url == f"{api.PROM_URL}/api/v1/query"
        assert params == {"query": 'chakra_energy{chakra="root"}'}

        class DummyResp:
            def raise_for_status(self) -> None:  # pragma: no cover - simple
                return None

            def json(self) -> dict:
                return {"data": {"result": [{"value": [0, "7"]}]}}

        return DummyResp()

    monkeypatch.setattr(api, "requests", SimpleNamespace(get=fake_get))

    with TestClient(app) as client:
        resp = client.get("/metrics/root")
    assert resp.status_code == 200
    assert resp.json() == {"chakra": "root", "value": 7.0}


def test_advice_endpoint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    app = create_app()
    advice_path = tmp_path / "advice.jsonl"
    monkeypatch.setattr(api, "ADVICE_PATH", advice_path)

    with TestClient(app) as client:
        resp = client.post("/advice/crown", json={"advice": "Relax"})
    assert resp.status_code == 200
    lines = advice_path.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["chakra"] == "crown"
    assert entry["advice"] == "Relax"
    assert "timestamp" in entry
