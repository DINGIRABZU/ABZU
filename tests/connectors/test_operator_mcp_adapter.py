import asyncio
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

from tests.conftest import allow_test

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "connectors" / "operator_mcp_adapter.py"
PACKAGE_PATH = MODULE_PATH.parent

connectors_pkg = ModuleType("connectors")
connectors_pkg.__path__ = [str(PACKAGE_PATH)]
sys.modules.setdefault("connectors", connectors_pkg)

allow_test(__file__)

SPEC = importlib.util.spec_from_file_location(
    "connectors.operator_mcp_adapter", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
adapter = importlib.util.module_from_spec(SPEC)
sys.modules["connectors.operator_mcp_adapter"] = adapter
SPEC.loader.exec_module(adapter)  # type: ignore[misc]


def test_ensure_handshake_stores_session(monkeypatch):
    async def fake_handshake(client):
        return {"session": {"id": "sess-1"}, "accepted_contexts": ["stage-b-rehearsal"]}

    called = {}

    async def fake_send(payload, **kwargs):
        called["payload"] = payload
        called["kwargs"] = kwargs

    monkeypatch.setattr(adapter, "operator_api_handshake", fake_handshake)
    monkeypatch.setattr(adapter, "operator_api_send_heartbeat", fake_send)

    conn = adapter.OperatorMCPAdapter()
    result = asyncio.run(conn.ensure_handshake())
    assert result["session"]["id"] == "sess-1"

    payload = asyncio.run(
        conn.emit_stage_b_heartbeat(
            {"ping": 1}, credential_expiry=datetime.now(timezone.utc)
        )
    )
    assert payload["ping"] == 1
    assert called["kwargs"]["session"]["id"] == "sess-1"


def test_emit_stage_b_heartbeat_reuses_session(monkeypatch):
    async def fake_handshake(client):
        return {
            "session": {
                "id": "sess-2",
                "credential_expiry": "2025-01-01T00:00:00Z",
            }
        }

    captured = {}

    async def fake_send(payload, **kwargs):
        captured["payload"] = payload
        captured["kwargs"] = kwargs

    monkeypatch.setattr(adapter, "operator_api_handshake", fake_handshake)
    monkeypatch.setattr(adapter, "operator_api_send_heartbeat", fake_send)

    conn = adapter.OperatorMCPAdapter()
    asyncio.run(conn.emit_stage_b_heartbeat({"pulse": "ok"}))

    assert captured["payload"]["pulse"] == "ok"
    assert captured["kwargs"]["session"]["id"] == "sess-2"


def test_rotation_drill_logging(monkeypatch, tmp_path):
    log_path = tmp_path / "rotation.jsonl"
    index_path = tmp_path / "CONNECTOR_INDEX.md"
    audit_path = tmp_path / "operator_mcp_audit.md"

    index_path.write_text(
        "MCP adapter stub references operator_mcp_audit.md", encoding="utf-8"
    )
    audit_path.write_text("audit", encoding="utf-8")

    monkeypatch.setattr(adapter, "_ROTATION_LOG", log_path)
    monkeypatch.setattr(adapter, "_CONNECTOR_INDEX", index_path)
    monkeypatch.setattr(adapter, "_AUDIT_DOC", audit_path)
    monkeypatch.setattr(adapter, "operator_api_doctrine", lambda: (True, []))
    monkeypatch.setattr(adapter, "operator_upload_doctrine", lambda: (True, []))
    monkeypatch.setattr(adapter, "crown_doctrine", lambda: (True, []))

    entry = adapter.record_rotation_drill(
        "operator_api",
        rotated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        handshake={
            "echo": {
                "rotation": {
                    "last_rotated": "2025-01-01T00:00:00Z",
                    "rotation_window": "PT48H",
                }
            }
        },
    )
    assert entry["rotation_window"]["duration"] == "PT48H"
    assert entry["rotation_window"]["window_id"].endswith("-PT48H")
    history = adapter.load_rotation_history()
    assert history == [entry]

    ok, failures = adapter.evaluate_operator_doctrine()
    assert ok, failures


def test_collect_transport_parity_artifacts_reports_stage_c_trial():
    entries = adapter.collect_transport_parity_artifacts()
    assert entries, "expected Stage C parity artifacts"
    latest = entries[-1]
    assert latest["parity"] is True
    assert latest["differences"] == []
    assert latest["rest_checksum"] == latest["grpc_checksum"]
    gaps = set(latest["monitoring_gaps"])
    expected_alerts = {
        "rest_latency_missing",
        "grpc_latency_missing",
        "heartbeat_missing",
    }
    assert expected_alerts <= gaps
    assert latest["heartbeat_emitted"] is False
    assert latest["rest_path"].endswith("rest_handshake_with_expiry.json")
    assert latest["grpc_path"].endswith("grpc_trial_handshake.json")
    assert latest["diff_path"].endswith("rest_grpc_handshake_diff.json")
    assert latest["metadata"]["rotation_window"]["rotation_window"] == "PT48H"


def test_build_transport_parity_monitoring_payload_surface_alerts():
    payload = adapter.build_transport_parity_monitoring_payload()
    assert payload["parity"] is True
    assert payload["checksum_match"] is True
    assert payload["rest_checksum"] == payload["grpc_checksum"]
    alerts = set(payload["alerts"])
    expected_alerts = {
        "rest_latency_missing",
        "grpc_latency_missing",
        "heartbeat_missing",
    }
    assert expected_alerts <= alerts
    assert payload["heartbeat_emitted"] is False
    assert payload["summary_path"].endswith("20251031T000000Z-test/summary.json")
