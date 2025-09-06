"""Tests for operator_service.api."""

import json
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

import operator_service.api as api
from operator_service.api import app
from razar import boot_orchestrator, status_dashboard


@pytest.fixture
def client() -> Iterable[TestClient]:
    """Return TestClient for operator service."""
    with TestClient(app) as c:
        yield c


def test_start_ignition_streams(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[str] = []

    def fake_start() -> Iterable[str]:
        called.append("yes")
        yield json.dumps({"boot": "ok"})

    monkeypatch.setattr(boot_orchestrator, "start", fake_start)
    resp = client.post("/start_ignition")
    assert resp.status_code == 200
    assert called == ["yes"]
    assert json.loads(resp.text) == {"boot": "ok"}


def test_status_returns_components(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        status_dashboard,
        "_component_statuses",
        lambda: [{"name": "comp", "status": "up"}],
    )
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json() == {"components": [{"name": "comp", "status": "up"}]}


def test_query_returns_results(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(api, "query_memory", lambda q: {"res": "ok"})
    resp = client.post("/query", json={"query": "hi"})
    assert resp.status_code == 200
    assert resp.json() == {"res": "ok"}


def test_memory_query_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = {
        "cortex": [],
        "vector": [],
        "spiral": "",
        "failed_layers": [],
    }
    monkeypatch.setattr(api, "query_memory", lambda q: expected)
    resp = client.get("/memory/query", params={"prompt": "hi"})
    assert resp.status_code == 200
    assert resp.json() == expected


def test_memory_query_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(_: str) -> dict:
        raise RuntimeError("nope")

    monkeypatch.setattr(api, "query_memory", boom)
    resp = client.get("/memory/query", params={"prompt": "hi"})
    assert resp.status_code == 500
