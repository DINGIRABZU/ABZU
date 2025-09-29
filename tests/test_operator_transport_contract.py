"""Dual-transport contract tests for operator_api."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Iterator, Mapping

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from connectors.operator_mcp_adapter import (
    collect_transport_parity_artifacts,
    compute_handshake_checksum,
)
import operator_api
from operator_api_grpc import OperatorApiGrpcService


STAGE_E_CONNECTORS: tuple[str, ...] = (
    "operator_api",
    "operator_upload",
    "crown_handshake",
)


def _load_stage_c_trial_entries() -> list[dict[str, Any]]:
    """Return transport parity entries using Stage C trial artifacts.

    The helper prefers ``collect_transport_parity_artifacts`` but also
    understands the newer Stage C summary layout where the handshake
    artifacts live at the top level of ``summary.json``.
    """

    entries = collect_transport_parity_artifacts()
    if entries:
        return entries

    stage_c_root = Path("logs") / "stage_c"
    trial_entries: list[dict[str, Any]] = []
    for summary_path in sorted(stage_c_root.glob("*/summary.json")):
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        summary = data.get("summary")
        if not isinstance(summary, dict):
            continue
        rest_path = summary.get("rest_handshake_with_expiry")
        grpc_path = summary.get("grpc_trial_handshake")
        diff_path = summary.get("rest_grpc_diff")
        if not all(isinstance(p, str) and p for p in (rest_path, grpc_path, diff_path)):
            continue
        trial_entries.append(
            {
                "run_id": summary_path.parent.name,
                "rest_path": rest_path,
                "grpc_path": grpc_path,
                "diff_path": diff_path,
                "summary": summary,
                "handshake_parity": (
                    data.get("handshake_parity")
                    if isinstance(data.get("handshake_parity"), dict)
                    else {}
                ),
            }
        )
    return trial_entries


def _load_json(path_hint: str) -> Mapping[str, Any] | None:
    path = Path(path_hint)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _iter_stage_c_summaries() -> Iterator[dict[str, Any]]:
    stage_c_root = Path("logs") / "stage_c"
    for summary_path in sorted(stage_c_root.glob("*/summary.json")):
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        yield data


def _rest_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = FastAPI()
    app.include_router(operator_api.router)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs" / "operators").mkdir(parents=True)
    client = TestClient(app)
    return client


class _DummyContext:
    """Minimal context stub capturing metadata for gRPC handler tests."""

    def __init__(self) -> None:
        self.trailing_metadata: tuple[tuple[str, str], ...] | None = None

    async def abort(self, status_code, details):
        raise RuntimeError(f"abort: {status_code}: {details}")

    def set_trailing_metadata(self, metadata):
        if metadata is None:
            self.trailing_metadata = None
        else:
            self.trailing_metadata = tuple(metadata)

    # The remaining gRPC context hooks are no-ops for these tests
    def set_code(self, _code):
        return None

    def set_details(self, _details):
        return None

    def send_initial_metadata(self, _metadata):
        return None

    def set_compression(self, _compression):
        return None

    def disable_next_message_compression(self):
        return None

    async def write(self, _response):
        return None

    async def read(self):
        return None


def test_grpc_rest_command_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _run() -> None:
        client = _rest_client(tmp_path, monkeypatch)
        service = OperatorApiGrpcService()
        try:
            rest_response = client.post(
                "/operator/command",
                json={"operator": "crown", "agent": "razar", "command": "status"},
            )
            assert rest_response.status_code == 200
            rest_body = rest_response.json()
            context = _DummyContext()
            grpc_body = await service._dispatch_command(
                {"operator": "crown", "agent": "razar", "command": "status"},
                context,
            )
        finally:
            client.close()
        assert rest_body["result"] == grpc_body["result"]
        assert rest_body["result"] == {"ack": "status"}
        assert rest_body["command_id"]
        assert grpc_body["command_id"]

    asyncio.run(_run())


def test_grpc_fallback_emits_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _run() -> None:
        client = _rest_client(tmp_path, monkeypatch)
        calls: dict[str, Any] = {"count": 0}
        original_dispatch = operator_api._dispatcher.dispatch

        def _patched_dispatch(*args: Any, **kwargs: Any) -> Any:
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("grpc failure")
            return original_dispatch(*args, **kwargs)

        monkeypatch.setattr(operator_api._dispatcher, "dispatch", _patched_dispatch)
        service = OperatorApiGrpcService(enable_rest_fallback=True)
        try:
            context = _DummyContext()
            body = await service._dispatch_command(
                {"operator": "crown", "agent": "razar", "command": "status"},
                context,
            )
        finally:
            client.close()
        assert body["result"] == {"ack": "status"}
        assert context.trailing_metadata == (("abzu-fallback", "rest"),)
        assert calls["count"] == 2

    asyncio.run(_run())


def test_stage_c_transport_parity_checksums_align() -> None:
    entries = _load_stage_c_trial_entries()
    assert entries, "expected Stage C transport parity artifacts"
    latest = entries[-1]

    rest_payload = _load_json(latest["rest_path"])
    grpc_payload = _load_json(latest["grpc_path"])
    diff_payload = _load_json(latest["diff_path"])

    assert isinstance(rest_payload, Mapping)
    assert isinstance(grpc_payload, Mapping)
    assert isinstance(diff_payload, Mapping)

    rest_normalized = rest_payload.get("normalized")
    if not isinstance(rest_normalized, Mapping):
        rest_normalized = rest_payload.get("handshake")
    grpc_normalized = grpc_payload.get("handshake_equivalent")
    if not isinstance(grpc_normalized, Mapping):
        grpc_normalized = grpc_payload.get("handshake")

    assert rest_normalized == grpc_normalized
    rest_checksum = compute_handshake_checksum(rest_normalized)
    grpc_checksum = compute_handshake_checksum(grpc_normalized)

    assert rest_checksum == grpc_checksum
    assert rest_checksum == diff_payload.get("rest_checksum")
    assert grpc_checksum == diff_payload.get("grpc_checksum")
    assert diff_payload.get("parity") is True
    assert diff_payload.get("differences") == []
    assert diff_payload.get("checksum_match") is True


def test_stage_e_connector_parity_coverage_pending() -> None:
    connectors_seen: set[str] = set()
    for data in _iter_stage_c_summaries():
        handshake_sources = []
        summary_section = data.get("summary")
        if isinstance(summary_section, Mapping):
            handshake_sources.append(summary_section.get("handshake"))
        handshake_parity = data.get("handshake_parity")
        if isinstance(handshake_parity, Mapping):
            handshake_sources.append(handshake_parity.get("rotation_window"))
        metrics = data.get("metrics")
        if isinstance(metrics, Mapping):
            handshake_sources.append(metrics.get("handshake"))

        for source in handshake_sources:
            if not isinstance(source, Mapping):
                continue
            rotation = source.get("rotation")
            if isinstance(rotation, Mapping):
                connector_id = rotation.get("connector_id")
                if isinstance(connector_id, str):
                    connectors_seen.add(connector_id)
            connector_id = source.get("connector_id")
            if isinstance(connector_id, str):
                connectors_seen.add(connector_id)

    missing = sorted({c for c in STAGE_E_CONNECTORS if c not in connectors_seen})
    assert missing == ["crown_handshake", "operator_upload"], missing


def test_stage_e_transport_monitoring_gaps_acknowledged() -> None:
    entries = _load_stage_c_trial_entries()
    assert entries, "expected Stage C transport parity artifacts"
    latest_summary = entries[-1]["summary"]
    assert isinstance(latest_summary, Mapping)

    trial_trace = latest_summary.get("trial_trace")
    rest_trace = trial_trace.get("rest") if isinstance(trial_trace, Mapping) else None
    grpc_trace = trial_trace.get("grpc") if isinstance(trial_trace, Mapping) else None

    missing_metrics = set()
    if not isinstance(rest_trace, Mapping) or rest_trace.get("latency_ms") is None:
        missing_metrics.add("rest_latency_missing")
    if not isinstance(grpc_trace, Mapping) or grpc_trace.get("latency_ms") is None:
        missing_metrics.add("grpc_latency_missing")
    if not latest_summary.get("heartbeat_emitted"):
        missing_metrics.add("heartbeat_missing")
    heartbeat_payload = latest_summary.get("heartbeat_payload")
    if not heartbeat_payload or not isinstance(heartbeat_payload, Mapping):
        missing_metrics.add("heartbeat_latency_missing")

    assert missing_metrics == {
        "rest_latency_missing",
        "grpc_latency_missing",
        "heartbeat_missing",
        "heartbeat_latency_missing",
    }
