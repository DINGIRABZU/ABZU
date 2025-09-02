"""Tests for operator api."""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import operator_api

__version__ = "0.1.0"


@pytest.fixture
def client(tmp_path: Path, monkeypatch) -> TestClient:
    """Return a test client with isolated upload directory."""

    app = FastAPI()
    app.include_router(operator_api.router)
    monkeypatch.chdir(tmp_path)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_dispatch(monkeypatch):
    """Patch dispatcher to control remote agent responses."""

    def _mock(*, result=None, error: str | None = None):
        def dispatch(operator, agent, func, *args, **kwargs):
            if error is not None:
                raise PermissionError(error)
            return result if result is not None else func(*args, **kwargs)

        monkeypatch.setattr(operator_api._dispatcher, "dispatch", dispatch)

    return _mock


def test_command_dispatches(client: TestClient, mock_dispatch) -> None:
    mock_dispatch(result={"ack": "noop"})
    resp = client.post(
        "/operator/command",
        json={"operator": "overlord", "agent": "crown", "command": "noop"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"result": {"ack": "noop"}}


def test_command_requires_fields(client: TestClient) -> None:
    resp = client.post("/operator/command", json={"operator": "overlord"})
    assert resp.status_code == 400


def test_upload_stores_and_forwards(client: TestClient, monkeypatch) -> None:
    captured: dict[str, dict] = {}

    def dispatch(operator, agent, func, *args):
        if operator == "overlord" and agent == "crown":
            return func(*args)
        if operator == "crown" and agent == "razar":
            captured["meta"] = args[0]
            return {"ok": True}
        raise AssertionError("unexpected dispatch")

    monkeypatch.setattr(operator_api._dispatcher, "dispatch", dispatch)
    resp = client.post(
        "/operator/upload",
        data={"operator": "overlord", "metadata": json.dumps({"x": 1})},
        files={"files": ("a.txt", b"hi")},
    )
    assert resp.status_code == 200
    assert resp.json()["stored"] == ["overlord/a.txt"]
    assert captured["meta"] == {"x": 1, "files": ["overlord/a.txt"]}
    assert (Path("uploads") / "overlord" / "a.txt").read_text() == "hi"


def test_upload_invalid_metadata(client: TestClient) -> None:
    resp = client.post(
        "/operator/upload",
        data={"operator": "overlord", "metadata": "not json"},
        files={"files": ("a.txt", b"hi")},
    )
    assert resp.status_code == 400


def test_upload_permission_error(client: TestClient, mock_dispatch) -> None:
    mock_dispatch(error="denied")
    resp = client.post(
        "/operator/upload",
        data={"operator": "overlord", "metadata": "{}"},
        files={"files": ("a.txt", b"hi")},
    )
    assert resp.status_code == 403


def test_command_permission_error(client: TestClient, mock_dispatch) -> None:
    mock_dispatch(error="nope")
    resp = client.post(
        "/operator/command",
        json={"operator": "overlord", "agent": "crown", "command": "noop"},
    )
    assert resp.status_code == 403


def test_upload_metadata_only(client: TestClient, monkeypatch) -> None:
    captured: dict[str, dict] = {}

    def dispatch(operator, agent, func, meta):
        if operator == "overlord" and agent == "crown":
            return func(meta)
        if operator == "crown" and agent == "razar":
            captured["meta"] = meta
            return {"ok": True}
        raise AssertionError("unexpected dispatch")

    monkeypatch.setattr(operator_api._dispatcher, "dispatch", dispatch)
    resp = client.post(
        "/operator/upload",
        data={"operator": "overlord", "metadata": json.dumps({"x": 1})},
    )
    assert resp.status_code == 200
    assert resp.json()["stored"] == []
    assert captured["meta"] == {"x": 1, "files": []}
