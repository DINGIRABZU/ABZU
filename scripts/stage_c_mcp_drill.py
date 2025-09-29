#!/usr/bin/env python3
"""Stage C MCP drill capturing handshake and heartbeat artifacts."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts._stage_runtime import bootstrap

bootstrap()

from connectors.operator_mcp_adapter import (
    ROTATION_WINDOW_HOURS,
    OperatorMCPAdapter,
    normalize_handshake_for_trace,
    compute_handshake_checksum,
    record_rotation_drill,
)
from connectors.operator_api_stage_b import (
    build_handshake_payload as build_operator_api_handshake,
)

LOGGER = logging.getLogger(__name__)

_EVENT_NAME = "stage-c4-operator-mcp-drill"
_STUB_ENV_FLAG = "ABZU_STAGE_C_MCP_DRILL_STUB"


def _normalize_contexts(value: Any) -> list[dict[str, Any]]:
    """Return ``value`` coerced into a list of context dictionaries."""

    results: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        for key, entry in value.items():
            if isinstance(entry, Mapping):
                payload = {"name": key, **dict(entry)}
                results.append(payload)
    elif isinstance(value, (list, tuple)):
        for entry in value:
            if isinstance(entry, Mapping):
                results.append(dict(entry))
            elif isinstance(entry, str):
                results.append({"name": entry, "status": "accepted"})
    return results


def _annotate_contexts(
    handshake: Mapping[str, Any] | None,
    *,
    handshake_path: str | None = None,
    summary_path: str | None = None,
) -> list[dict[str, Any]]:
    """Return accepted contexts with evidence metadata applied."""

    if not isinstance(handshake, Mapping):
        return []

    contexts = _normalize_contexts(handshake.get("accepted_contexts"))
    if not contexts:
        return []

    for entry in contexts:
        entry.setdefault("status", "accepted")
        entry.setdefault("accepted_via", _EVENT_NAME)
        if handshake_path:
            entry.setdefault("evidence_path", handshake_path)
        if summary_path:
            entry.setdefault("summary_path", summary_path)

    return list(contexts)


def _context_status_from(contexts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return a mapping from context name to metadata for ``contexts``."""

    indexed: dict[str, dict[str, Any]] = {}
    for entry in contexts:
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            continue
        indexed[name] = {key: value for key, value in entry.items() if key != "name"}
    return indexed


def _use_stub_adapter() -> bool:
    flag = os.getenv(_STUB_ENV_FLAG, "")
    return flag.lower() in {"1", "true", "yes", "on"}


def _build_stub_handshake(now: datetime) -> dict[str, Any]:
    rotation_window = f"PT{ROTATION_WINDOW_HOURS}H"
    rotated_at = _isoformat(now)
    rotation_metadata = {
        "connector_id": "operator_api",
        "last_rotated": rotated_at,
        "rotation_window": rotation_window,
        "window_id": f"{now.strftime('%Y%m%dT%H%M%SZ')}-{rotation_window}",
    }
    expiry = _isoformat(now + timedelta(hours=ROTATION_WINDOW_HOURS))
    return {
        "authenticated": True,
        "session": {
            "id": "stage-c-session",
            "credential_expiry": expiry,
        },
        "accepted_contexts": [
            {"name": "stage-b-rehearsal", "status": "accepted"},
            {"name": "stage-c-prep", "status": "accepted"},
        ],
        "rotation": rotation_metadata,
        "echo": {"rotation": dict(rotation_metadata)},
    }


class _StubOperatorAdapter:
    """In-memory adapter when the MCP gateway is unavailable."""

    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self._handshake = _build_stub_handshake(now)

    async def ensure_handshake(self) -> dict[str, Any]:
        LOGGER.info("Using stubbed Stage C MCP drill payload")
        LOGGER.debug("Stub handshake payload: %s", self._handshake)
        return dict(self._handshake)

    async def emit_stage_b_heartbeat(
        self,
        payload: dict[str, Any],
        *,
        credential_expiry: datetime | None = None,
    ) -> dict[str, Any]:
        heartbeat_payload = dict(payload)
        heartbeat_payload.setdefault("event", _EVENT_NAME)
        session = self._handshake.get("session", {})
        heartbeat_payload.setdefault("session", session)

        expiry_candidate: datetime | None = None
        if isinstance(credential_expiry, datetime):
            expiry_candidate = credential_expiry
        elif isinstance(session, dict):
            raw_expiry = session.get("credential_expiry")
            if isinstance(raw_expiry, str) and raw_expiry:
                try:
                    expiry_candidate = datetime.fromisoformat(
                        raw_expiry.replace("Z", "+00:00")
                    )
                except ValueError:
                    expiry_candidate = None

        if expiry_candidate is None:
            expiry_candidate = datetime.now(timezone.utc) + timedelta(
                hours=ROTATION_WINDOW_HOURS
            )

        heartbeat_payload["credential_expiry"] = _isoformat(expiry_candidate)
        return heartbeat_payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir",
        help="Directory where handshake and heartbeat artifacts will be stored.",
    )
    parser.add_argument(
        "--skip-heartbeat",
        action="store_true",
        help="Do not emit the rehearsal heartbeat during the drill.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the drill summary as JSON (default when stdout is captured).",
    )
    return parser


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _build_trace_bundle(
    handshake: dict[str, Any] | None,
    *,
    gateway_base: str,
) -> dict[str, Any]:
    request_payload: dict[str, Any] | None = None
    try:
        request_payload = build_operator_api_handshake()
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.warning("unable to build operator_api handshake payload", exc_info=True)

    normalized = normalize_handshake_for_trace(handshake)
    checksum = compute_handshake_checksum(handshake)
    contexts = [
        entry.get("name")
        for entry in normalized.get("accepted_contexts", [])
        if isinstance(entry, dict)
    ]

    rest_trace = {
        "method": "POST",
        "endpoint": f"{gateway_base}/handshake",
        "request": request_payload,
        "response": handshake,
        "normalized": normalized,
        "checksum": checksum,
    }

    grpc_trace = {
        "service": "neoabzu.vector.VectorService",
        "method": "Init",
        "rpc": "neoabzu.vector.VectorService/Init",
        "request": {
            "stage": "C",
            "connector_id": "operator_api",
            "contexts": contexts,
        },
        "response": {
            "message": "stage C trial handshake parity",
            "handshake_equivalent": normalized,
        },
        "metadata": {
            "parity_checksum": checksum,
            "credential_expiry": (
                normalized.get("session", {}).get("credential_expiry")
                if isinstance(normalized.get("session"), dict)
                else None
            ),
            "rotation_window": normalized.get("rotation"),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "mode": "trial",
        },
    }

    return {"rest": rest_trace, "grpc": grpc_trace}


async def _run_drill(
    output_dir: Path,
    *,
    emit_heartbeat: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    adapter: OperatorMCPAdapter | _StubOperatorAdapter
    if _use_stub_adapter():
        adapter = _StubOperatorAdapter()
    else:
        adapter = OperatorMCPAdapter()
    handshake_raw = await adapter.ensure_handshake()
    handshake: dict[str, Any]
    if isinstance(handshake_raw, Mapping):
        handshake = dict(handshake_raw)
    else:
        handshake = {}

    heartbeat_payload: dict[str, Any] | None = None
    credential_expiry: datetime | None = None
    if emit_heartbeat:
        credential_expiry = datetime.now(timezone.utc) + timedelta(
            hours=ROTATION_WINDOW_HOURS
        )
        heartbeat_payload = await adapter.emit_stage_b_heartbeat(
            {
                "event": _EVENT_NAME,
                "stage": "C",
            },
            credential_expiry=credential_expiry,
        )

    handshake_path = output_dir / "mcp_handshake.json"
    annotated_contexts = _annotate_contexts(
        handshake,
        handshake_path=str(handshake_path),
    )
    if annotated_contexts:
        handshake["accepted_contexts"] = annotated_contexts

    handshake_path.write_text(
        json.dumps(handshake, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    heartbeat_path = output_dir / "heartbeat.json"
    heartbeat_record = {
        "event": _EVENT_NAME,
        "payload": heartbeat_payload,
        "credential_expiry": _isoformat(credential_expiry),
        "rotation_window_hours": ROTATION_WINDOW_HOURS,
    }
    heartbeat_path.write_text(
        json.dumps(heartbeat_record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Record the rotation drill so doctrine checks account for this run.
    gateway_base = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001").rstrip("/")
    traces = _build_trace_bundle(
        handshake if isinstance(handshake, dict) else None, gateway_base=gateway_base
    )

    context_status = _context_status_from(annotated_contexts)
    record_rotation_drill(
        "operator_api",
        rotated_at=None,
        handshake=handshake,
        context_status=context_status if context_status else None,
        traces=traces,
    )

    summary = {
        "status": "success",
        "event": _EVENT_NAME,
        "handshake_path": str(handshake_path),
        "heartbeat_path": str(heartbeat_path),
        "rotation_window_hours": ROTATION_WINDOW_HOURS,
        "credential_expiry": heartbeat_record["credential_expiry"],
        "heartbeat_emitted": heartbeat_payload is not None,
        "handshake": handshake,
        "heartbeat_payload": heartbeat_payload,
        "trial_trace": traces,
    }

    return summary


async def _async_main(args: argparse.Namespace) -> int:
    try:
        summary = await _run_drill(
            Path(args.output_dir), emit_heartbeat=not args.skip_heartbeat
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("Stage C MCP drill failed: %s", exc)
        return 1

    output = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.json:
        print(output)
    else:
        print("Stage C MCP drill completed.")
        print(output)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_async_main(args))


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
