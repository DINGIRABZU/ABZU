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


def configure_subprocess(
    monkeypatch: pytest.MonkeyPatch,
    *,
    stdout: bytes = b"",
    stderr: bytes = b"",
    returncode: int = 0,
) -> None:
    """Replace subprocess execution with a dummy process returning canned output."""

    class DummyProcess:
        def __init__(self) -> None:
            self.returncode = returncode

        async def communicate(self) -> tuple[bytes, bytes]:
            return stdout, stderr

    async def fake_create_subprocess_exec(*args: Any, **kwargs: Any) -> DummyProcess:
        return DummyProcess()

    monkeypatch.setattr(
        operator_api.asyncio,
        "create_subprocess_exec",
        fake_create_subprocess_exec,
    )


def test_command_dispatches(
    client: TestClient, mock_dispatch: Callable[..., None]
) -> None:
    mock_dispatch(result={"ack": "noop"})
    resp = client.post(
        "/operator/command",
        json={"operator": "overlord", "agent": "crown", "command": "noop"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == {"ack": "noop"}
    assert "command_id" in body


def test_command_requires_fields(client: TestClient) -> None:
    resp = client.post("/operator/command", json={"operator": "overlord"})
    assert resp.status_code == 400


def test_upload_stores_and_forwards(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, dict] = {}

    def dispatch(
        operator: str,
        agent: str,
        func: Callable[..., dict],
        *args: Any,
        **kwargs: Any,
    ) -> dict:
        kwargs.pop("command_id", None)
        if operator == "overlord" and agent == "crown":
            return func(*args, **kwargs)
        if operator == "crown" and agent == "razar":
            meta = args[0]
            captured["meta"] = meta
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
    meta = captured["meta"]
    assert meta["x"] == 1
    assert meta["files"] == ["overlord/a.txt"]
    assert "command_id" in meta
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
        operator: str,
        agent: str,
        func: Callable[..., dict],
        meta: dict,
        **kwargs: Any,
    ) -> dict:
        kwargs.pop("command_id", None)
        if operator == "overlord" and agent == "crown":
            return func(meta, **kwargs)
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
    meta = captured["meta"]
    assert meta["x"] == 1
    assert meta["files"] == []
    assert "command_id" in meta


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
        ack = ws.receive_json()
        assert ack["event"] == "ack"
        assert ack["command"] == "noop"
        assert "command_id" in ack
        progress = ws.receive_json()
        assert progress["event"] == "progress"
        assert progress["command"] == "noop"
        assert progress["percent"] == 100


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
        operator_api.boot_orchestrator,
        "start",
        lambda: called.setdefault("ok", True),
        raising=False,
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


def test_stage_b1_memory_proof_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = {
        "dataset": "data/vector_memory_scaling/corpus.jsonl",
        "total_records": 120,
        "queries_timed": 115,
        "init_duration_s": 1.23,
        "latency_p50_s": 0.01,
        "latency_p95_s": 0.05,
        "latency_p99_s": 0.09,
        "layers": {"total": 4, "ready": 4, "failed": 0},
        "query_failures": 0,
    }
    stdout = ("INFO stage\n" + json.dumps(summary, indent=2) + "\n").encode("utf-8")
    configure_subprocess(monkeypatch, stdout=stdout)

    resp = client.post("/alpha/stage-b1-memory-proof")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    metrics = body["metrics"]
    assert metrics["latency_ms"]["p95"] == 50.0
    assert metrics["layers"]["total"] == 4
    assert Path(body["log_dir"]).exists()


def test_stage_b1_memory_proof_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_subprocess(
        monkeypatch,
        stdout=b"",
        stderr=b"boom",
        returncode=1,
    )

    resp = client.post("/alpha/stage-b1-memory-proof")
    assert resp.status_code == 500
    detail = resp.json()["detail"].lower()
    assert "exited with code 1" in detail


def test_stage_b2_sonic_rehearsal_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet = {
        "generated_at": "2025-09-22T10:15:54Z",
        "stage": "B",
        "context": "stage-b-rehearsal",
        "connectors": {
            "operator_api": {
                "module": "connectors.operator_api_stage_b",
                "doctrine_ok": True,
                "supported_channels": ["handshake", "heartbeat"],
                "capabilities": ["register"],
                "handshake_response": {
                    "accepted_contexts": ["stage-b-rehearsal"],
                },
            }
        },
    }
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    packet_path = logs_dir / "stage_b_rehearsal_packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    configure_subprocess(monkeypatch, stdout=b"packet\n")

    resp = client.post("/alpha/stage-b2-sonic-rehearsal")
    assert resp.status_code == 200
    body = resp.json()
    metrics = body["metrics"]
    assert metrics["connectors"]["operator_api"]["doctrine_ok"] is True
    copied = Path(body["log_dir"]) / "stage_b_rehearsal_packet.json"
    assert copied.exists()


def test_stage_b2_sonic_rehearsal_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_subprocess(monkeypatch, stdout=b"", stderr=b"fail", returncode=2)
    resp = client.post("/alpha/stage-b2-sonic-rehearsal")
    assert resp.status_code == 500
    assert "exited with code 2" in resp.json()["detail"].lower()


def test_stage_b3_connector_rotation_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = {
        "stage": "B",
        "targets": ["operator_api"],
        "handshake": {
            "accepted_contexts": ["stage-b-rehearsal"],
            "session": {"id": "sess-1"},
        },
        "doctrine_ok": True,
        "doctrine_failures": [],
    }
    stdout = (json.dumps(result, indent=2) + "\n").encode("utf-8")
    rotation_log = Path("logs") / "stage_b_rotation_drills.jsonl"
    rotation_log.parent.mkdir(exist_ok=True)
    rotation_log.write_text(json.dumps({"connector_id": "operator_api"}) + "\n")
    configure_subprocess(monkeypatch, stdout=stdout)

    resp = client.post("/alpha/stage-b3-connector-rotation")
    assert resp.status_code == 200
    body = resp.json()
    metrics = body["metrics"]
    assert metrics["accepted_contexts"] == ["stage-b-rehearsal"]
    copied = Path(body["log_dir"]) / "stage_b_rotation_drills.jsonl"
    assert copied.exists()


def test_stage_b3_connector_rotation_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_subprocess(monkeypatch, stdout=b"", stderr=b"err", returncode=3)
    resp = client.post("/alpha/stage-b3-connector-rotation")
    assert resp.status_code == 500
    assert "exited with code 3" in resp.json()["detail"].lower()
