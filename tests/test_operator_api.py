"""Tests for operator api."""

import json
from pathlib import Path
from typing import Any, Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import operator_api

__version__ = "0.1.0"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Return a test client with isolated upload directory."""

    app = FastAPI()
    app.include_router(operator_api.router)
    monkeypatch.chdir(tmp_path)
    operator_api._event_clients.clear()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_dispatch(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Patch dispatcher to control remote agent responses."""

    def _mock(*, result: dict | None = None, error: str | None = None) -> None:
        def dispatch(
            operator: str,
            agent: str,
            func: Callable[..., dict],
            *args: Any,
            **kwargs: Any,
        ) -> dict:
            if error is not None:
                raise PermissionError(error)
            return result if result is not None else func(*args, **kwargs)

        monkeypatch.setattr(operator_api._dispatcher, "dispatch", dispatch)

    return _mock


def test_command_dispatches(
    client: TestClient, mock_dispatch: Callable[..., None]
) -> None:
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


def test_upload_stores_and_forwards(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, dict] = {}

    def dispatch(
        operator: str, agent: str, func: Callable[..., dict], *args: Any
    ) -> dict:
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


def test_upload_permission_error(
    client: TestClient, mock_dispatch: Callable[..., None]
) -> None:
    mock_dispatch(error="denied")
    resp = client.post(
        "/operator/upload",
        data={"operator": "overlord", "metadata": "{}"},
        files={"files": ("a.txt", b"hi")},
    )
    assert resp.status_code == 403


def test_command_permission_error(
    client: TestClient, mock_dispatch: Callable[..., None]
) -> None:
    mock_dispatch(error="nope")
    resp = client.post(
        "/operator/command",
        json={"operator": "overlord", "agent": "crown", "command": "noop"},
    )
    assert resp.status_code == 403


def test_upload_metadata_only(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, dict] = {}

    def dispatch(
        operator: str, agent: str, func: Callable[..., dict], meta: dict
    ) -> dict:
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


def test_events_websocket(
    client: TestClient, mock_dispatch: Callable[..., None]
) -> None:
    """WebSocket receives command acknowledgement and progress."""

    mock_dispatch(result={"ack": "noop"})
    with client.websocket_connect("/operator/events") as ws:
        resp = client.post(
            "/operator/command",
            json={"operator": "overlord", "agent": "crown", "command": "noop"},
        )
        assert resp.status_code == 200
        assert ws.receive_json() == {"event": "ack", "command": "noop"}
        assert ws.receive_json() == {
            "event": "progress",
            "command": "noop",
            "percent": 100,
        }


def test_status_endpoint(client: TestClient, tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "razar_mission.log").write_text("error: boom\nok\n")
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    (mem_dir / "item.txt").write_text("data")
    resp = client.get("/operator/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "components" in body
    assert body["errors"] == ["error: boom"]
    assert body["memory"]["files"] == 1


def test_register_and_unregister_servant_model(client: TestClient) -> None:
    """Operator can register and remove servant models at runtime."""

    resp = client.post(
        "/operator/models",
        json={"name": "echo", "command": ["bash", "-lc", "cat"]},
    )
    assert resp.status_code == 200
    assert "echo" in resp.json()["models"]

    resp = client.delete("/operator/models/echo")
    assert resp.status_code == 200
    assert "echo" not in resp.json()["models"]


def test_start_ignition_endpoint(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: dict[str, bool] = {}
    monkeypatch.setattr(
        operator_api.boot_orchestrator, "start", lambda: called.setdefault("ok", True)
    )
    resp = client.post("/start_ignition")
    assert resp.status_code == 200
    assert resp.json() == {"status": "started"}
    assert called["ok"]


def test_memory_query_endpoint(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(operator_api, "query_memory", lambda q: {"res": q})
    resp = client.post("/memory/query", json={"query": "demo"})
    assert resp.status_code == 200
    assert resp.json() == {"results": {"res": "demo"}}


def test_handover_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(operator_api.ai_invoker, "handover", lambda c, e: True)
    resp = client.post("/handover", json={"component": "c", "error": "boom"})
    assert resp.status_code == 200
    assert resp.json() == {"handover": True}
