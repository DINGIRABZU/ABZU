"""Tests for operator api."""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

_dummy_omegaconf = ModuleType("omegaconf")
_dummy_omegaconf.OmegaConf = object  # type: ignore[attr-defined]
_dummy_omegaconf.DictConfig = object  # type: ignore[attr-defined]
sys.modules.setdefault("omegaconf", _dummy_omegaconf)

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
    on_spawn: Callable[[tuple[Any, ...]], None] | None = None,
) -> None:
    """Replace subprocess execution with a dummy process returning canned output."""

    class DummyProcess:
        def __init__(self) -> None:
            self.returncode = returncode

        async def communicate(self) -> tuple[bytes, bytes]:
            return stdout, stderr

    async def fake_create_subprocess_exec(*args: Any, **kwargs: Any) -> DummyProcess:
        if on_spawn is not None:
            on_spawn(args)
        return DummyProcess()

    monkeypatch.setattr(
        operator_api.asyncio,
        "create_subprocess_exec",
        fake_create_subprocess_exec,
    )


def _load_summary(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_stage_a1_boot_telemetry_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stage A1 reports success even when environment-limited warnings surface."""

    configure_subprocess(
        monkeypatch,
        stdout=b"bootstrap complete\n",
        stderr=b"environment-limited: missing optional faiss\n",
        returncode=0,
    )

    resp = client.post("/alpha/stage-a1-boot-telemetry")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "environment-limited" in body.get("stderr", "")

    summary = _load_summary(body["summary_path"])
    assert summary["status"] == "success"
    assert "environment-limited" in summary.get("stderr", "")


def test_stage_a2_crown_replays_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stage A2 capture succeeds with environment-limited stderr preserved."""

    configure_subprocess(
        monkeypatch,
        stdout=b"crown replay bundle saved\n",
        stderr=b"environment-limited: numpy shim active\n",
        returncode=0,
    )

    resp = client.post("/alpha/stage-a2-crown-replays")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "environment-limited" in body.get("stderr", "")

    summary = _load_summary(body["summary_path"])
    assert summary["status"] == "success"
    assert "environment-limited" in summary.get("stderr", "")


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
    repo_root = Path(operator_api.__file__).resolve().parent
    rotation_log = repo_root / "logs" / "stage_b_rotation_drills.jsonl"
    rotation_log.parent.mkdir(parents=True, exist_ok=True)
    original_text = (
        rotation_log.read_text(encoding="utf-8") if rotation_log.exists() else ""
    )
    rotation_log.write_text(json.dumps({"connector_id": "operator_api"}) + "\n")

    recorded: dict[str, Any] = {}

    def _simulate_spawn(args: tuple[Any, ...]) -> None:
        recorded["args"] = args
        entry = {
            "connector_id": "operator_api",
            "rotated_at": "2025-10-01T00:00:00Z",
            "window_hours": operator_api.ROTATION_WINDOW_HOURS,
        }
        with rotation_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    configure_subprocess(monkeypatch, stdout=stdout, on_spawn=_simulate_spawn)

    log_dir_path: Path | None = None
    try:
        resp = client.post("/alpha/stage-b3-connector-rotation")
        assert resp.status_code == 200
        body = resp.json()
        metrics = body["metrics"]
        assert metrics["accepted_contexts"] == ["stage-b-rehearsal"]
        log_dir_path = Path(body["log_dir"])
        copied = log_dir_path / "stage_b_rotation_drills.jsonl"
        assert copied.exists()
        args = recorded.get("args")
        assert args is not None
        assert Path(args[1]) == repo_root / "scripts" / "stage_b_smoke.py"
        ledger_lines = rotation_log.read_text(encoding="utf-8").splitlines()
        assert any("2025-10-01T00:00:00Z" in line for line in ledger_lines)
    finally:
        if log_dir_path and log_dir_path.exists():
            shutil.rmtree(log_dir_path, ignore_errors=True)
        if original_text:
            rotation_log.write_text(original_text, encoding="utf-8")
        else:
            rotation_log.unlink(missing_ok=True)


def test_stage_b3_connector_rotation_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_subprocess(monkeypatch, stdout=b"", stderr=b"err", returncode=3)
    resp = client.post("/alpha/stage-b3-connector-rotation")
    assert resp.status_code == 500
    assert "exited with code 3" in resp.json()["detail"].lower()


def test_stage_c1_exit_checklist_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_subprocess(
        monkeypatch,
        stdout=b"All checklist items are marked complete.\n",
    )
    resp = client.post("/alpha/stage-c1-exit-checklist")
    assert resp.status_code == 200
    body = resp.json()
    assert body["metrics"]["completed"] is True
    assert body["metrics"]["unchecked_count"] == 0
    assert body["metrics"]["failing_count"] == 0
    assert body["metrics"]["failing_items"] == []
    assert Path(body["log_dir"]).exists()


def test_stage_c1_exit_checklist_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    stdout = (
        "Unchecked items in absolute_protocol_checklist.md:\n- [ ] pending item\n"
    ).encode("utf-8")
    configure_subprocess(
        monkeypatch,
        stdout=stdout,
        returncode=1,
    )
    resp = client.post("/alpha/stage-c1-exit-checklist")
    assert resp.status_code == 500
    assert "checklist" in resp.json()["detail"]


def test_stage_c1_exit_checklist_checked_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    stdout = b"- [x] item resolved (Status: failed)\n"
    configure_subprocess(
        monkeypatch,
        stdout=stdout,
    )
    resp = client.post("/alpha/stage-c1-exit-checklist")
    assert resp.status_code == 500
    assert "failing items" in resp.json()["detail"].lower()


def test_stage_c1_metrics_marks_failing_status(tmp_path: Path) -> None:
    payload: dict[str, Any] = {"status": "success"}
    stdout = """
    - [x] item one (Status: blocked)
    - [x] item two (status: failed)
    """.strip()
    metrics = operator_api._stage_c1_metrics(stdout, "", tmp_path, payload)
    assert metrics["failing_count"] == 2
    assert metrics["completed"] is False
    assert payload["status"] == "error"
    assert payload["error"] == "checklist contains failing items"


def test_stage_c2_demo_storyline_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _create_demo(args: tuple[Any, ...]) -> None:
        for index, arg in enumerate(args):
            if isinstance(arg, str) and arg.endswith("stage_c_scripted_demo.py"):
                output_dir = Path(args[index + 1])
                telemetry = output_dir / "telemetry"
                emotion = output_dir / "emotion"
                telemetry.mkdir(parents=True, exist_ok=True)
                emotion.mkdir(parents=True, exist_ok=True)
                summary = {
                    "timestamp": "2025-09-21T17:35:46Z",
                    "steps": 3,
                    "max_sync_offset_s": 0.067,
                    "dropouts_detected": False,
                }
                (telemetry / "summary.json").write_text(
                    json.dumps(summary), encoding="utf-8"
                )
                (telemetry / "run_summary.json").write_text("{}", encoding="utf-8")
                (telemetry / "media_manifest.json").write_text("[]", encoding="utf-8")
                (telemetry / "events.jsonl").write_text("{}\n", encoding="utf-8")
                (emotion / "stream.jsonl").write_text("{}\n", encoding="utf-8")
                break

    configure_subprocess(
        monkeypatch,
        stdout=b"demo\n",
        on_spawn=_create_demo,
    )
    resp = client.post("/alpha/stage-c2-demo-storyline")
    assert resp.status_code == 200
    body = resp.json()
    metrics = body["metrics"]
    assert metrics["summary"]["steps"] == 3
    assert metrics["media_manifest"].endswith("media_manifest.json")
    assert Path(body["log_dir"]).exists()


def test_stage_c2_demo_storyline_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_subprocess(
        monkeypatch,
        stdout=b"",
        stderr=b"boom",
        returncode=2,
    )
    resp = client.post("/alpha/stage-c2-demo-storyline")
    assert resp.status_code == 500
    assert "demo summary missing" in resp.json()["detail"].lower()


def test_stage_c3_readiness_sync_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage_a_dir = Path("logs") / "stage_a" / "20240101T000000Z-stage"
    stage_b_dir = Path("logs") / "stage_b" / "20240102T000000Z-stage"
    stage_a_dir.mkdir(parents=True, exist_ok=True)
    stage_b_dir.mkdir(parents=True, exist_ok=True)
    (stage_a_dir / "summary.json").write_text(
        json.dumps({"run_id": "a", "status": "success", "completed_at": "2024"}),
        encoding="utf-8",
    )
    (stage_b_dir / "summary.json").write_text(
        json.dumps({"run_id": "b", "status": "success", "completed_at": "2024"}),
        encoding="utf-8",
    )
    configure_subprocess(monkeypatch, stdout=b"ready\n")
    resp = client.post("/alpha/stage-c3-readiness-sync")
    assert resp.status_code == 200
    body = resp.json()
    merged = body["metrics"]["merged"]
    assert merged["latest_runs"] == {"stage_a": "a", "stage_b": "b"}


def test_stage_c3_readiness_sync_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_subprocess(monkeypatch, stdout=b"ready\n")
    resp = client.post("/alpha/stage-c3-readiness-sync")
    assert resp.status_code == 500
    assert "missing readiness" in resp.json()["detail"]


def test_stage_c4_operator_mcp_drill_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class DummyAdapter:
        async def emit_stage_b_heartbeat(
            self, payload: dict, credential_expiry: Any
        ) -> None:
            self.payload = payload

    adapter = DummyAdapter()

    async def _ensure_ready() -> None:
        operator_api._MCP_ADAPTER = adapter
        operator_api._MCP_SESSION = {"session": {"id": "sess-1"}}
        operator_api._LAST_CREDENTIAL_EXPIRY = datetime.now(timezone.utc)

    monkeypatch.setattr(operator_api, "_ensure_mcp_ready_for_request", _ensure_ready)
    repo_root = Path(operator_api.__file__).resolve().parent
    recorded: dict[str, Any] = {}

    def _simulate(args: tuple[Any, ...]) -> None:
        recorded["args"] = args
        output_dir = Path(args[-1])
        output_dir.mkdir(parents=True, exist_ok=True)
        handshake_path = output_dir / "mcp_handshake.json"
        heartbeat_path = output_dir / "heartbeat.json"
        handshake_payload = {
            "session": {
                "id": "sess-1",
                "credential_expiry": "2025-12-01T00:00:00Z",
            },
            "accepted_contexts": ["stage-b-rehearsal"],
        }
        handshake_path.write_text(
            json.dumps(handshake_payload),
            encoding="utf-8",
        )
        heartbeat_path.write_text(
            json.dumps(
                {
                    "event": "stage-c4-operator-mcp-drill",
                    "payload": {"ok": True},
                    "credential_expiry": "2025-12-01T00:00:00Z",
                    "rotation_window_hours": operator_api.ROTATION_WINDOW_HOURS,
                }
            ),
            encoding="utf-8",
        )

    configure_subprocess(monkeypatch, stdout=b"drill\n", on_spawn=_simulate)
    log_dir_path: Path | None = None
    try:
        resp = client.post("/alpha/stage-c4-operator-mcp-drill")
        assert resp.status_code == 200
        body = resp.json()
        metrics = body["metrics"]
        assert metrics["handshake"]["session"]["id"] == "sess-1"
        assert metrics["heartbeat_emitted"] is True
        log_dir_path = Path(body["log_dir"])
        assert log_dir_path.exists()
        args = recorded.get("args")
        assert args is not None
        assert Path(args[1]) == repo_root / "scripts" / "stage_c_mcp_drill.py"
    finally:
        if log_dir_path and log_dir_path.exists():
            shutil.rmtree(log_dir_path, ignore_errors=True)
        operator_api._MCP_ADAPTER = None
        operator_api._MCP_SESSION = None
        operator_api._LAST_CREDENTIAL_EXPIRY = None


def test_stage_c4_operator_mcp_drill_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raise() -> None:
        raise HTTPException(status_code=503, detail="handshake failed")

    monkeypatch.setattr(operator_api, "_ensure_mcp_ready_for_request", _raise)
    configure_subprocess(monkeypatch, stdout=b"drill\n")
    resp = client.post("/alpha/stage-c4-operator-mcp-drill")
    assert resp.status_code == 500
    assert resp.json()["detail"] == "handshake failed"
