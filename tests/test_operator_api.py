"""Tests for operator api."""

import asyncio
import inspect
import json
import os
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
    monkeypatch.setattr(operator_api, "_STAGE_A_ROOT", Path("logs") / "stage_a")
    monkeypatch.setattr(operator_api, "_STAGE_B_ROOT", Path("logs") / "stage_b")
    monkeypatch.setattr(operator_api, "_STAGE_C_ROOT", Path("logs") / "stage_c")
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
    on_spawn: Callable[[tuple[Any, ...], dict[str, Any]], None] | None = None,
) -> None:
    """Replace subprocess execution with a dummy process returning canned output."""

    class DummyProcess:
        def __init__(self) -> None:
            self.returncode = returncode

        async def communicate(self) -> tuple[bytes, bytes]:
            return stdout, stderr

    async def fake_create_subprocess_exec(*args: Any, **kwargs: Any) -> DummyProcess:
        if on_spawn is not None:
            call_with_kwargs = True
            try:
                signature = inspect.signature(on_spawn)
            except (TypeError, ValueError):
                call_with_kwargs = True
            else:
                params = list(signature.parameters.values())
                positional = [
                    p
                    for p in params
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                ]
                has_var_positional = any(p.kind == p.VAR_POSITIONAL for p in params)
                if len(positional) < 2 and not has_var_positional:
                    call_with_kwargs = False
            if call_with_kwargs:
                on_spawn(args, kwargs)
            else:
                on_spawn(args)
        return DummyProcess()

    monkeypatch.setattr(
        operator_api.asyncio,
        "create_subprocess_exec",
        fake_create_subprocess_exec,
    )


def _load_summary(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _configure_stage_readiness_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import aggregate_stage_readiness as readiness_aggregate

    monkeypatch.setattr(readiness_aggregate, "STAGE_A_ROOT", Path("logs") / "stage_a")
    monkeypatch.setattr(readiness_aggregate, "STAGE_B_ROOT", Path("logs") / "stage_b")
    monkeypatch.setattr(readiness_aggregate, "REPO_ROOT", Path.cwd())


def test_run_stage_workflow_parses_pretty_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Multi-line JSON summaries are reconstructed from stdout tail."""

    structured = {
        "status": "success",
        "summary": {"checks": ["alpha", "beta"]},
        "warnings": ["environment-limited dependency"],
    }
    stdout_text = "\n".join(
        [
            "INFO stage: preparing summary payload",
            json.dumps(structured, indent=2),
            "INFO stage: emitted summary payload",
        ]
    )
    configure_subprocess(
        monkeypatch,
        stdout=f"{stdout_text}\n".encode("utf-8"),
        stderr=b"",
        returncode=0,
    )

    payload = asyncio.run(
        operator_api._run_stage_workflow(
            tmp_path / "stage_a",
            "stage_a_test",
            ["python", "-m", "fake_module"],
        )
    )

    assert isinstance(payload["summary"], dict)
    assert payload["summary"] == structured
    assert isinstance(payload["summary"]["summary"], dict)


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


def test_stage_a_env_injection_and_module_isolation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stage A workflows inject sandbox env vars and work without cached modules."""

    monkeypatch.setenv("PYTHONPATH", "/legacy/path")
    monkeypatch.setenv("ABZU_SANDBOX_OVERRIDES", "sandbox=beta")

    captured_envs: list[dict[str, Any]] = []

    def on_spawn(_args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        env = kwargs.get("env")
        assert env is not None
        captured_envs.append(env)

    configure_subprocess(
        monkeypatch,
        stdout=b"ok\n",
        stderr=b"",
        returncode=0,
        on_spawn=on_spawn,
    )

    monkeypatch.delitem(sys.modules, "scripts.bootstrap", raising=False)
    monkeypatch.delitem(sys.modules, "scripts.crown_capture_replays", raising=False)

    resp_boot = client.post("/alpha/stage-a1-boot-telemetry")
    resp_replays = client.post("/alpha/stage-a2-crown-replays")

    assert resp_boot.status_code == 200
    assert resp_replays.status_code == 200
    assert resp_boot.json()["status"] == "success"
    assert resp_replays.json()["status"] == "success"

    repo_prefix = [str(operator_api._REPO_ROOT)]
    src_dir = operator_api._REPO_ROOT / "src"
    if src_dir.exists():
        repo_prefix.append(str(src_dir))

    assert len(captured_envs) >= 2
    for env in captured_envs:
        assert env["ABZU_FORCE_STAGE_SANDBOX"] == "1"
        assert env.get("ABZU_SANDBOX_OVERRIDES") == "sandbox=beta"
        pythonpath_parts = env["PYTHONPATH"].split(os.pathsep)
        assert pythonpath_parts[: len(repo_prefix)] == repo_prefix
        assert os.pathsep.join(pythonpath_parts[len(repo_prefix) :]) == "/legacy/path"


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


def test_status_endpoint(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "razar_mission.log").write_text("error: boom\nok\n")
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    (mem_dir / "item.txt").write_text("data")
    monkeypatch.setattr(operator_api, "_REPO_ROOT", Path.cwd())
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
    sys.modules.pop("neoabzu_memory", None)
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
        "stubbed_bundle": True,
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
    assert metrics["stubbed_bundle"] is True
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
        summary_text = body["summary"]
        assert metrics["accepted_contexts"] == ["stage-b-rehearsal"]
        assert metrics["rotation_summary"] == summary_text
        assert "Rotated" in summary_text
        assert "operator_api" in summary_text
        log_dir_path = Path(body["log_dir"])
        copied = log_dir_path / "stage_b_rotation_drills.jsonl"
        assert copied.exists()
        args = recorded.get("args")
        assert args is not None
        assert Path(args[1]) == repo_root / "scripts" / "stage_b_smoke.py"
        ledger_entries = [
            json.loads(line)
            for line in rotation_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert any(
            entry.get("rotated_at") == "2025-10-01T00:00:00Z"
            for entry in ledger_entries
        )
        latest_entry = ledger_entries[-1]
        assert latest_entry.get("rotation_summary") == summary_text
        assert "credential_expiry" not in latest_entry
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
    shutil.rmtree(Path("logs"), ignore_errors=True)
    _configure_stage_readiness_paths(monkeypatch)

    stage_a1_dir = Path("logs") / "stage_a" / "20240101T000000Z-stage_a1_boot_telemetry"
    stage_a2_dir = Path("logs") / "stage_a" / "20240101T000500Z-stage_a2_crown_replays"
    stage_a3_dir = Path("logs") / "stage_a" / "20240101T001000Z-stage_a3_gate_shakeout"
    stage_b1_dir = Path("logs") / "stage_b" / "20240102T000000Z-stage_b1_memory_proof"
    stage_b2_dir = (
        Path("logs") / "stage_b" / "20240102T000500Z-stage_b2_sonic_rehearsal"
    )
    stage_b3_dir = (
        Path("logs") / "stage_b" / "20240102T001000Z-stage_b3_connector_rotation"
    )

    for directory in (
        stage_a1_dir,
        stage_a2_dir,
        stage_a3_dir,
        stage_b1_dir,
        stage_b2_dir,
        stage_b3_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    for slug_dir, run_id, stage_name, completed in (
        (stage_a1_dir, "a1-run", "stage_a1_boot_telemetry", "2024-01-01T00:10:00Z"),
        (stage_a2_dir, "a2-run", "stage_a2_crown_replays", "2024-01-01T00:15:00Z"),
        (stage_a3_dir, "a3-run", "stage_a3_gate_shakeout", "2024-01-01T00:20:00Z"),
    ):
        (slug_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "success",
                    "completed_at": completed,
                    "stage": stage_name,
                }
            ),
            encoding="utf-8",
        )

    rotation_window = {
        "window_id": "win-1",
        "started_at": "2024-01-01T00:00:00Z",
        "expires_at": "2024-01-03T00:00:00Z",
    }
    rotation_summary = (
        "Rotated operator_api/operator_upload (doctrine ok); "
        "window win-1; rotation expires 2024-01-03T00:00:00Z; "
        "credentials expire 2024-01-03T00:00:00Z"
    )

    (stage_b1_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "b1-run",
                "status": "success",
                "completed_at": "2024-01-02T00:10:00Z",
                "stage": "stage_b1_memory_proof",
                "metrics": {
                    "rotation_window": rotation_window,
                    "rotation_summary": rotation_summary,
                    "heartbeat_expiry": "2024-01-03T00:00:00Z",
                },
            }
        ),
        encoding="utf-8",
    )
    for slug_dir, run_id, stage_name in (
        (stage_b2_dir, "b2-run", "stage_b2_sonic_rehearsal"),
        (stage_b3_dir, "b3-run", "stage_b3_connector_rotation"),
    ):
        (slug_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "success",
                    "completed_at": "2024-01-02T00:20:00Z",
                    "stage": stage_name,
                }
            ),
            encoding="utf-8",
        )

    resp = client.post("/alpha/stage-c3-readiness-sync")
    assert resp.status_code == 200
    body = resp.json()
    merged = body["metrics"]["merged"]
    assert merged["overall_status"] == "ready"
    assert merged["latest_runs"]["stage_a"] == {
        "A1": "a1-run",
        "A2": "a2-run",
        "A3": "a3-run",
    }
    assert merged["latest_runs"]["stage_b"] == "b1-run"
    assert merged["status_flags"]["stage_a"] == "success"
    assert merged["status_flags"]["stage_b"] == "success"
    rotation_section = merged.get("rotation")
    assert rotation_section is not None
    assert rotation_section["summary"] == rotation_summary
    assert rotation_section["window"] == rotation_window
    assert rotation_section["credential_expiry"] == "2024-01-03T00:00:00Z"

    artifacts = body["artifacts"]
    readiness_bundle = Path(artifacts["readiness_bundle"])
    readiness_summary = Path(artifacts["readiness_summary"])
    assert readiness_bundle.exists()
    assert readiness_summary.exists()
    assert Path(body["summary_path"]) == readiness_summary


def test_stage_c3_readiness_sync_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_stage_readiness_paths(monkeypatch)
    resp = client.post("/alpha/stage-c3-readiness-sync")
    assert resp.status_code == 500
    assert "missing readiness" in resp.json()["detail"]


def _write_successful_stage_b_slugs(root: Path) -> None:
    stage_b1_dir = root / "20240102T000000Z-stage_b1_memory_proof"
    stage_b2_dir = root / "20240102T000500Z-stage_b2_sonic_rehearsal"
    stage_b3_dir = root / "20240102T001000Z-stage_b3_connector_rotation"
    for directory in (stage_b1_dir, stage_b2_dir, stage_b3_dir):
        directory.mkdir(parents=True, exist_ok=True)
    (stage_b1_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "b1-run",
                "status": "success",
                "completed_at": "2024-01-02T01:05:00Z",
                "stage": "stage_b1_memory_proof",
            }
        ),
        encoding="utf-8",
    )
    for slug_dir, run_id, stage_name in (
        (stage_b2_dir, "b2-run", "stage_b2_sonic_rehearsal"),
        (stage_b3_dir, "b3-run", "stage_b3_connector_rotation"),
    ):
        (slug_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "success",
                    "completed_at": "2024-01-02T01:10:00Z",
                    "stage": stage_name,
                }
            ),
            encoding="utf-8",
        )


def test_stage_c3_readiness_sync_requires_attention_when_stage_a_slug_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    shutil.rmtree(Path("logs"), ignore_errors=True)
    _configure_stage_readiness_paths(monkeypatch)
    stage_a_root = Path("logs") / "stage_a"
    stage_b_root = Path("logs") / "stage_b"
    stage_a1_dir = stage_a_root / "20240101T010000Z-stage_a1_boot_telemetry"
    stage_a2_dir = stage_a_root / "20240101T010500Z-stage_a2_crown_replays"
    stage_a3_dir = stage_a_root / "20240101T011000Z-stage_a3_gate_shakeout"
    for directory in (stage_a1_dir, stage_a2_dir, stage_a3_dir):
        directory.mkdir(parents=True, exist_ok=True)
    (stage_a1_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "a1-failure",
                "status": "error",
                "completed_at": "2024-01-01T01:05:00Z",
                "stage": "stage_a1_boot_telemetry",
                "error": "boot telemetry failed",
                "stderr_tail": ["traceback..."],
            }
        ),
        encoding="utf-8",
    )
    for slug_dir, run_id, stage_name in (
        (stage_a2_dir, "a2-run", "stage_a2_crown_replays"),
        (stage_a3_dir, "a3-run", "stage_a3_gate_shakeout"),
    ):
        (slug_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "success",
                    "completed_at": "2024-01-01T01:10:00Z",
                    "stage": stage_name,
                }
            ),
            encoding="utf-8",
        )

    _write_successful_stage_b_slugs(stage_b_root)

    resp = client.post("/alpha/stage-c3-readiness-sync")
    assert resp.status_code == 500
    detail = resp.json()["detail"]
    assert "requires_attention" in detail


def test_stage_c3_readiness_sync_requires_attention_for_upstream_risk_notes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    shutil.rmtree(Path("logs"), ignore_errors=True)
    _configure_stage_readiness_paths(monkeypatch)
    stage_a_root = Path("logs") / "stage_a"
    stage_b_root = Path("logs") / "stage_b"
    for slug, stage_name in (
        ("A1", "stage_a1_boot_telemetry"),
        ("A2", "stage_a2_crown_replays"),
        ("A3", "stage_a3_gate_shakeout"),
    ):
        run_dir = stage_a_root / f"20240101T020000Z-{stage_name}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": f"{slug.lower()}-run",
                    "status": "success",
                    "completed_at": "2024-01-01T02:10:00Z",
                    "stage": stage_name,
                }
            ),
            encoding="utf-8",
        )

    stage_b1_dir = stage_b_root / "20240102T020000Z-stage_b1_memory_proof"
    stage_b2_dir = stage_b_root / "20240102T020500Z-stage_b2_sonic_rehearsal"
    stage_b3_dir = stage_b_root / "20240102T021000Z-stage_b3_connector_rotation"
    for directory in (stage_b1_dir, stage_b2_dir, stage_b3_dir):
        directory.mkdir(parents=True, exist_ok=True)
    (stage_b1_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "b1-run",
                "status": "success",
                "completed_at": "2024-01-02T02:10:00Z",
                "stage": "stage_b1_memory_proof",
                "warnings": ["connector latency requires review"],
            }
        ),
        encoding="utf-8",
    )
    for slug_dir, run_id, stage_name in (
        (stage_b2_dir, "b2-run", "stage_b2_sonic_rehearsal"),
        (stage_b3_dir, "b3-run", "stage_b3_connector_rotation"),
    ):
        (slug_dir / "summary.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "success",
                    "completed_at": "2024-01-02T02:15:00Z",
                    "stage": stage_name,
                }
            ),
            encoding="utf-8",
        )

    resp = client.post("/alpha/stage-c3-readiness-sync")
    assert resp.status_code == 500
    detail = resp.json()["detail"]
    assert "requires_attention" in detail


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

    repo_rotation_log_path = (
        Path(operator_api._REPO_ROOT) / "logs" / "stage_b_rotation_drills.jsonl"
    )
    repo_rotation_log_path.parent.mkdir(parents=True, exist_ok=True)
    rotation_log_backup = None
    if repo_rotation_log_path.exists():
        rotation_log_backup = repo_rotation_log_path.read_text(encoding="utf-8")
    rotation_entry = {
        "connector_id": "operator_api",
        "rotated_at": "2024-05-01T00:00:00Z",
        "window_hours": operator_api.ROTATION_WINDOW_HOURS,
        "rotation_window": {
            "window_id": "20240501T000000Z-PT48H",
            "started_at": "2024-05-01T00:00:00Z",
            "expires_at": "2024-05-03T00:00:00Z",
            "duration": "PT48H",
        },
    }
    repo_rotation_log_path.write_text(
        json.dumps(rotation_entry) + "\n", encoding="utf-8"
    )

    def _simulate(args: tuple[Any, ...]) -> None:
        recorded["args"] = args
        output_dir = Path(args[-2])
        output_dir.mkdir(parents=True, exist_ok=True)
        handshake_path = output_dir / "mcp_handshake.json"
        heartbeat_path = output_dir / "heartbeat.json"
        handshake_payload = {
            "session": {
                "id": "sess-1",
                "credential_expiry": "2025-12-01T00:00:00Z",
            },
            "accepted_contexts": ["stage-b-rehearsal"],
            "rotation": rotation_entry["rotation_window"],
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
        assert metrics["rotation_window_verified"] is True
        assert metrics["rotation_window_id"] == "20240501T000000Z-PT48H"
        log_dir_path = Path(body["log_dir"])
        assert log_dir_path.exists()
        args = recorded.get("args")
        assert args is not None
        assert Path(args[1]) == repo_root / "scripts" / "stage_c_mcp_drill.py"
        artifacts = body["artifacts"]
        handshake_artifact = Path(artifacts["mcp_handshake"])
        heartbeat_artifact = Path(artifacts["heartbeat"])
        rotation_artifact = Path(artifacts["rotation_metadata"])
        assert handshake_artifact.exists()
        assert heartbeat_artifact.exists()
        assert rotation_artifact.exists()
        rotation_payload = json.loads(rotation_artifact.read_text(encoding="utf-8"))
        assert (
            rotation_payload["rotation_window"]["window_id"] == "20240501T000000Z-PT48H"
        )
    finally:
        if log_dir_path and log_dir_path.exists():
            shutil.rmtree(log_dir_path, ignore_errors=True)
        if rotation_log_backup is not None:
            repo_rotation_log_path.write_text(rotation_log_backup, encoding="utf-8")
        elif repo_rotation_log_path.exists():
            repo_rotation_log_path.unlink()
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


def test_stage_c4_operator_mcp_drill_missing_artifacts(
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

    repo_rotation_log_path = (
        Path(operator_api._REPO_ROOT) / "logs" / "stage_b_rotation_drills.jsonl"
    )
    repo_rotation_log_path.parent.mkdir(parents=True, exist_ok=True)
    rotation_log_backup = None
    if repo_rotation_log_path.exists():
        rotation_log_backup = repo_rotation_log_path.read_text(encoding="utf-8")
    rotation_entry = {
        "connector_id": "operator_api",
        "rotated_at": "2024-05-01T00:00:00Z",
        "window_hours": operator_api.ROTATION_WINDOW_HOURS,
        "rotation_window": {
            "window_id": "20240501T000000Z-PT48H",
            "started_at": "2024-05-01T00:00:00Z",
            "expires_at": "2024-05-03T00:00:00Z",
            "duration": "PT48H",
        },
    }
    repo_rotation_log_path.write_text(
        json.dumps(rotation_entry) + "\n", encoding="utf-8"
    )

    def _simulate(args: tuple[Any, ...]) -> None:
        output_dir = Path(args[-2])
        output_dir.mkdir(parents=True, exist_ok=True)

    configure_subprocess(monkeypatch, stdout=b"drill\n", on_spawn=_simulate)
    try:
        resp = client.post("/alpha/stage-c4-operator-mcp-drill")
        assert resp.status_code == 500
        detail = resp.json()["detail"]
        assert "missing handshake artifact" in detail
    finally:
        if rotation_log_backup is not None:
            repo_rotation_log_path.write_text(rotation_log_backup, encoding="utf-8")
        elif repo_rotation_log_path.exists():
            repo_rotation_log_path.unlink()
        shutil.rmtree(Path("logs") / "stage_c", ignore_errors=True)
        operator_api._MCP_ADAPTER = None
        operator_api._MCP_SESSION = None
        operator_api._LAST_CREDENTIAL_EXPIRY = None
