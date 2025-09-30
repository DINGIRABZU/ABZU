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


def _latest_stage_e_summary() -> tuple[Mapping[str, Any], Path]:
    stage_e_root = Path("logs") / "stage_e"
    summary_paths = sorted(stage_e_root.glob("*/summary.json"))
    assert summary_paths, "expected Stage E transport snapshot"
    latest_path = summary_paths[-1]
    data = json.loads(latest_path.read_text(encoding="utf-8"))
    assert isinstance(data, Mapping)
    return data, latest_path


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
    summary, summary_path = _latest_stage_e_summary()
    connectors = summary.get("connectors")
    assert isinstance(connectors, Mapping), f"missing connectors in {summary_path}"

    missing = sorted({c for c in STAGE_E_CONNECTORS if c not in connectors})
    assert not missing, f"missing connectors: {missing}"

    telemetry_hashes = summary.get("telemetry_hashes")
    assert isinstance(telemetry_hashes, Mapping)

    for connector_id in STAGE_E_CONNECTORS:
        connector_entry = connectors.get(connector_id)
        assert isinstance(connector_entry, Mapping)
        assert connector_entry.get("parity") is True
        assert connector_entry.get("checksum_match") is True

        artifacts = connector_entry.get("artifacts")
        assert isinstance(artifacts, Mapping)
        for key in ("rest", "grpc", "diff"):
            artifact_path = artifacts.get(key)
            assert isinstance(artifact_path, str) and artifact_path
            assert Path(artifact_path).exists()

        telemetry = telemetry_hashes.get(connector_id)
        assert isinstance(telemetry, Mapping)
        rest_hash = telemetry.get("rest")
        grpc_hash = telemetry.get("grpc")
        assert isinstance(rest_hash, str) and rest_hash
        assert isinstance(grpc_hash, str) and grpc_hash
        assert rest_hash == connector_entry.get("rest_checksum")
        assert grpc_hash == connector_entry.get("grpc_checksum")


def test_stage_e_transport_monitoring_gaps_acknowledged() -> None:
    summary, _summary_path = _latest_stage_e_summary()
    connectors = summary.get("connectors")
    assert isinstance(connectors, Mapping)

    heartbeat_gaps = summary.get("heartbeat_gaps")
    assert isinstance(heartbeat_gaps, list)
    gap_set = {item for item in heartbeat_gaps if isinstance(item, str)}

    for connector_id in STAGE_E_CONNECTORS:
        connector_entry = connectors.get(connector_id)
        assert isinstance(connector_entry, Mapping)
        monitoring_gaps = connector_entry.get("monitoring_gaps")
        assert isinstance(monitoring_gaps, list)
        gap_labels = {item for item in monitoring_gaps if isinstance(item, str)}

        if connector_entry.get("heartbeat_emitted"):
            assert "heartbeat_missing" not in gap_labels
        else:
            assert "heartbeat_missing" in gap_labels
            assert connector_id in gap_set

        assert "rest_latency_missing" in gap_labels
        assert "grpc_latency_missing" in gap_labels
        assert "heartbeat_latency_missing" in gap_labels

    dashboard = summary.get("dashboard")
    assert isinstance(dashboard, Mapping)
    assert isinstance(dashboard.get("url"), str) and dashboard.get("url")
