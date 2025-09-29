"""Generate Stage B rehearsal packet for MCP connectors."""

from __future__ import annotations

import asyncio
import importlib
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
STUB_DIR = Path(__file__).resolve().parent / "_dependency_stubs"

# Ensure Stage B connectors treat MCP as enabled during the dry-run.
os.environ.setdefault("ABZU_USE_MCP", "1")
os.environ.setdefault("MCP_GATEWAY_URL", "https://mcp.test")

# Provide a minimal package stub so connector modules can resolve relative imports.
connectors_stub = types.ModuleType("connectors")
connectors_stub.__file__ = str(CONNECTORS_DIR / "__init__.py")
connectors_stub.__path__ = [str(CONNECTORS_DIR)]
sys.modules.setdefault("connectors", connectors_stub)


_OPTIONAL_DEPENDENCIES: dict[str, str] = {
    "torch": "PyTorch tensor runtime used by audio codecs",
    "simpleaudio": "Simpleaudio playback backend",
    "clap": "Contrastive Language-Audio Pretraining interface",
    "rave": "Realtime Audio Variational autoEncoder shim",
}

_dependency_imports: dict[str, dict[str, Any]] = {}


def _load_stub_module(name: str) -> types.ModuleType:
    """Import ``name`` from the local stub directory."""

    stub_path = STUB_DIR / name / "__init__.py"
    if not stub_path.exists():
        raise ImportError(f"fallback stub not available for {name}")
    spec = importlib.util.spec_from_file_location(name, stub_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load fallback stub for {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _import_optional_dependency(name: str) -> None:
    """Import ``name`` tracking whether the fallback stub was required."""

    if name in _dependency_imports:
        return

    error: str | None = None
    try:
        module = importlib.import_module(name)
        stubbed = False
    except Exception as exc:  # pragma: no cover - defensive import guard
        error = f"{exc.__class__.__name__}: {exc}"
        module = _load_stub_module(name)
        stubbed = True

    _dependency_imports[name] = {
        "module": module,
        "stubbed": stubbed or bool(getattr(module, "__ABZU_FALLBACK__", False)),
        "error": error,
    }


for dependency in _OPTIONAL_DEPENDENCIES:
    _import_optional_dependency(dependency)


def _dependency_status() -> list[dict[str, Any]]:
    """Return metadata describing optional dependency availability."""

    statuses: list[dict[str, Any]] = []
    for name, description in _OPTIONAL_DEPENDENCIES.items():
        record = _dependency_imports.get(name)
        if record is None:
            continue
        module = record["module"]
        module_path = getattr(module, "__file__", None)
        resolved_path = (
            str(Path(module_path).resolve()) if isinstance(module_path, str) else None
        )
        stubbed = bool(record.get("stubbed")) or bool(
            getattr(module, "__ABZU_FALLBACK__", False)
        )
        status = {
            "module": name,
            "description": description,
            "available": not stubbed,
            "stubbed": stubbed,
            "version": getattr(module, "__version__", None),
            "path": resolved_path,
        }
        if stubbed:
            status["notes"] = record.get("error") or "fallback stub injected"
        statuses.append(status)
    return statuses


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

    handshake_payload = module.build_handshake_payload()
    async with httpx.AsyncClient(transport=transport) as client:
        handshake_result = await module.handshake(client=client)
        heartbeat_result = await module.send_heartbeat(
            dict(heartbeat_payload),
            client=client,
            session=handshake_result.get("session"),
            credential_expiry=credential_expiry,
        )

    doctrine_ok, doctrine_failures = module.doctrine_compliant()

    recorded_handshake = state.get("handshake_request")
    if recorded_handshake is not None and recorded_handshake != handshake_payload:
        raise AssertionError("handshake payload mismatch during rehearsal capture")

    canonical_heartbeat = module.build_heartbeat_payload(
        dict(heartbeat_payload),
        session=handshake_result.get("session"),
        credential_expiry=credential_expiry,
    )

    heartbeats = state.get("heartbeats")
    if isinstance(heartbeats, list) and heartbeats:
        last_heartbeat = heartbeats[-1]
        if last_heartbeat != canonical_heartbeat:
            raise AssertionError("heartbeat payload mismatch during rehearsal capture")

    return {
        "connector_id": config.connector_id,
        "module": module.__name__,
        "handshake_request": handshake_payload,
        "handshake_response": handshake_result,
        "heartbeat_request": canonical_heartbeat,
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

    dependencies = _dependency_status()
    fallback_notes: list[str] = []
    for status in dependencies:
        if status.get("stubbed"):
            detail = status.get("notes")
            if detail and detail != "fallback stub injected":
                fallback_notes.append(
                    f"{status['module']}: fallback stub active ({detail})"
                )
            else:
                fallback_notes.append(f"{status['module']}: fallback stub active")

    if fallback_notes:
        for record in results.values():
            existing = list(record.get("fallbacks", []))
            existing.extend(fallback_notes)
            record["fallbacks"] = existing

    return {
        "generated_at": _iso_now(),
        "stage": "B",
        "context": neo_apsu_stage_b._STAGE_B_CONTEXT,
        "connectors": results,
        "dependencies": dependencies,
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
