"""Generate Stage B rehearsal packet for MCP connectors."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONNECTORS_DIR = ROOT / "connectors"

# Ensure Stage B connectors treat MCP as enabled during the dry-run.
os.environ.setdefault("ABZU_USE_MCP", "1")
os.environ.setdefault("MCP_GATEWAY_URL", "https://mcp.test")

# Provide a minimal package stub so connector modules can resolve relative imports.
connectors_stub = types.ModuleType("connectors")
connectors_stub.__file__ = str(CONNECTORS_DIR / "__init__.py")
connectors_stub.__path__ = [str(CONNECTORS_DIR)]
sys.modules.setdefault("connectors", connectors_stub)


def _load_connector_module(name: str, relative_path: str) -> Any:
    """Return the imported connector module without executing package side effects."""

    spec = importlib.util.spec_from_file_location(name, CONNECTORS_DIR / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load connector module: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


neo_apsu_stage_b = _load_connector_module(
    "connectors.neo_apsu_stage_b", "neo_apsu_stage_b.py"
)
operator_api_stage_b = _load_connector_module(
    "connectors.operator_api_stage_b", "operator_api_stage_b.py"
)
operator_upload_stage_b = _load_connector_module(
    "connectors.operator_upload_stage_b", "operator_upload_stage_b.py"
)
crown_handshake_stage_b = _load_connector_module(
    "connectors.crown_handshake_stage_b", "crown_handshake_stage_b.py"
)

OUTPUT_PATH = Path("logs") / "stage_b_rehearsal_packet.json"


def _iso_now() -> str:
    """Return the current UTC timestamp without microseconds."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _build_transport(
    *,
    context: str,
    session_id: str,
    credential_expiry: str,
) -> tuple[httpx.MockTransport, Dict[str, Any]]:
    """Return a mock transport capturing handshake and heartbeat payloads."""

    state: Dict[str, Any] = {"handshake_request": None, "heartbeats": []}

    def _handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if request.url.path.endswith("/handshake"):
            state["handshake_request"] = payload
            return httpx.Response(
                200,
                json={
                    "authenticated": True,
                    "session": {
                        "id": session_id,
                        "credential_expiry": credential_expiry,
                    },
                    "accepted_contexts": [context],
                },
            )
        if request.url.path.endswith("/heartbeat"):
            state.setdefault("heartbeats", []).append(payload)
            return httpx.Response(202, json={"status": "accepted"})
        raise AssertionError(f"unexpected MCP path: {request.url.path}")

    return httpx.MockTransport(_handler), state


async def _exercise_connector(
    module: Any,
    *,
    session_id: str,
    credential_expiry: str,
    heartbeat_payload: Dict[str, Any],
) -> dict[str, Any]:
    """Perform handshake and heartbeat against a mock MCP gateway."""

    config = module._CONNECTOR._config  # type: ignore[attr-defined]
    transport, state = _build_transport(
        context=config.context_name,
        session_id=session_id,
        credential_expiry=credential_expiry,
    )

    async with httpx.AsyncClient(transport=transport) as client:
        handshake_result = await module.handshake(client=client)
        heartbeat_result = await module.send_heartbeat(
            dict(heartbeat_payload),
            client=client,
            session=handshake_result.get("session"),
        )

    doctrine_ok, doctrine_failures = module.doctrine_compliant()

    heartbeat_request = None
    heartbeats = state.get("heartbeats")
    if isinstance(heartbeats, list) and heartbeats:
        heartbeat_request = heartbeats[-1]

    return {
        "connector_id": config.connector_id,
        "module": module.__name__,
        "handshake_request": state.get("handshake_request"),
        "handshake_response": handshake_result,
        "heartbeat_request": heartbeat_request,
        "heartbeat_payload": heartbeat_result,
        "doctrine_ok": doctrine_ok,
        "doctrine_failures": doctrine_failures,
        "supported_channels": list(config.supported_channels),
        "capabilities": list(config.capabilities),
    }


async def _generate_report() -> dict[str, Any]:
    """Return the rehearsal packet for the Stage B connectors."""

    targets = [
        (
            operator_api_stage_b,
            {
                "session_id": "sess-operator",
                "credential_expiry": "2025-12-01T00:00:00Z",
                "heartbeat_payload": {"status": "aligned"},
            },
        ),
        (
            operator_upload_stage_b,
            {
                "session_id": "sess-upload",
                "credential_expiry": "2025-12-01T00:00:00Z",
                "heartbeat_payload": {"status": "aligned"},
            },
        ),
        (
            crown_handshake_stage_b,
            {
                "session_id": "sess-crown",
                "credential_expiry": "2025-11-15T00:00:00Z",
                "heartbeat_payload": {"status": "mission-brief-ready"},
            },
        ),
    ]

    results = {}
    for module, params in targets:
        record = await _exercise_connector(module, **params)
        results[record["connector_id"]] = record

    return {
        "generated_at": _iso_now(),
        "stage": "B",
        "context": neo_apsu_stage_b._STAGE_B_CONTEXT,
        "connectors": results,
    }


def main() -> int:
    """Entry point for CLI execution."""

    report = asyncio.run(_generate_report())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Stage B rehearsal packet written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
