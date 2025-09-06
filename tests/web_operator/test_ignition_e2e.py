"""End-to-end tests for operator_service ignition route."""

import json
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

from operator_service.api import app
from razar import boot_orchestrator


@pytest.fixture
def client() -> Iterable[TestClient]:
    """Return TestClient that captures server errors as responses."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_ignition_success(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """RAZAR ignition streams logs and ends in success."""
    logs = [
        json.dumps({"step": "init"}),
        json.dumps({"status": "success"}),
    ]

    def fake_start() -> Iterable[str]:
        for item in logs:
            yield item

    monkeypatch.setattr(boot_orchestrator, "start", fake_start)
    resp = client.post("/start_ignition")
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines == logs
    assert json.loads(lines[-1])["status"] == "success"


def test_ignition_crown_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Crown failure propagates as server error."""

    def fail() -> Iterable[str]:  # pragma: no cover - failure path
        raise RuntimeError("crown offline")

    monkeypatch.setattr(boot_orchestrator, "start", fail)
    resp = client.post("/start_ignition")
    assert resp.status_code == 500
    assert resp.text == "Internal Server Error"
