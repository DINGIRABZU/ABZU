"""Tests for operator_service.api."""

import json
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

from operator_service.api import app
from razar import boot_orchestrator, ai_invoker, status_dashboard


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


def test_handover_streams(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, tuple[str, str]] = {}

    def fake_handover(component: str, error: str) -> Iterable[str]:
        captured["args"] = (component, error)
        yield json.dumps({"patched": True})

    monkeypatch.setattr(ai_invoker, "handover", fake_handover)
    resp = client.post("/handover", json={"component": "x", "error": "boom"})
    assert resp.status_code == 200
    assert captured["args"] == ("x", "boom")
    assert json.loads(resp.text) == {"patched": True}
