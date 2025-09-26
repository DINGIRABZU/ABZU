#!/usr/bin/env python3
"""Stage B rehearsal smoke checks for operator connectors."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from scripts._stage_runtime import bootstrap

bootstrap()

from connectors.operator_mcp_adapter import (
    ROTATION_WINDOW_HOURS,
    STAGE_B_TARGET_SERVICES,
    OperatorMCPAdapter,
    evaluate_operator_doctrine,
    record_rotation_drill,
    stage_b_context_enabled,
)

LOGGER = logging.getLogger(__name__)
_STUB_ENV_FLAG = "ABZU_STAGE_B_SMOKE_STUB"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-heartbeat",
        action="store_true",
        help="Do not emit the rehearsal heartbeat during the run.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results as JSON for downstream automation.",
    )
    return parser


def _isoformat(value: datetime) -> str:
    """Return ``value`` normalised to a ``Z``-suffixed ISO-8601 string."""

    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


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
            "id": "stage-b-session",
            "credential_expiry": expiry,
        },
        "accepted_contexts": [
            {"name": "stage-b-rehearsal", "status": "accepted"},
            {"name": "stage-c-prep", "status": "pending"},
        ],
        "rotation": rotation_metadata,
        "echo": {"rotation": dict(rotation_metadata)},
    }


class _StubOperatorAdapter:
    """In-memory adapter used when the MCP gateway is unavailable."""

    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self._handshake = _build_stub_handshake(now)

    async def ensure_handshake(self) -> dict[str, Any]:
        LOGGER.info("Using stubbed Stage B handshake payload")
        LOGGER.debug("Stub handshake payload: %s", self._handshake)
        return dict(self._handshake)

    async def emit_stage_b_heartbeat(
        self,
        payload: dict[str, Any],
        *,
        credential_expiry: datetime | None = None,
    ) -> dict[str, Any]:
        heartbeat_payload = dict(payload)
        heartbeat_payload.setdefault("event", "stage-b-smoke")
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


def _build_adapter() -> OperatorMCPAdapter | _StubOperatorAdapter:
    if _use_stub_adapter():
        return _StubOperatorAdapter()
    return OperatorMCPAdapter()


async def _run_operator_checks(
    *,
    emit_heartbeat: bool,
) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    adapter = _build_adapter()
    handshake_data = await adapter.ensure_handshake()

    heartbeat_payload: dict[str, Any] | None = None
    heartbeat_expiry_iso: str | None = None
    if emit_heartbeat:
        expiry = datetime.now(timezone.utc) + timedelta(hours=ROTATION_WINDOW_HOURS)
        heartbeat_payload = await adapter.emit_stage_b_heartbeat(
            {"event": "stage-b-smoke"}, credential_expiry=expiry
        )
        heartbeat_expiry_iso = _isoformat(expiry)

    return handshake_data, heartbeat_payload, heartbeat_expiry_iso


def _collect_crown_metadata() -> dict[str, Any]:
    from razar import crown_handshake

    return {
        "version": getattr(crown_handshake, "__version__", "unknown"),
        "module": getattr(crown_handshake, "__file__", "n/a"),
    }


async def run_stage_b_smoke(*, emit_heartbeat: bool = True) -> Dict[str, Any]:
    if not stage_b_context_enabled():
        raise RuntimeError("ABZU_USE_MCP=1 required for Stage B smoke checks")

    handshake, heartbeat_payload, heartbeat_expiry = await _run_operator_checks(
        emit_heartbeat=emit_heartbeat
    )

    gateway_base = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001").rstrip("/")

    results: Dict[str, Any] = {
        "stage": "B",
        "targets": list(STAGE_B_TARGET_SERVICES),
        "services": {
            "operator_api": {
                "session": handshake.get("session"),
                "accepted_contexts": handshake.get("accepted_contexts"),
            },
            "operator_upload": {
                "session_reused": True,
                "notes": "Upload operations share the operator MCP session.",
            },
            "crown_handshake": _collect_crown_metadata(),
        },
        "endpoints": {
            "gateway": gateway_base,
            "handshake": f"{gateway_base}/handshake",
            "heartbeat": f"{gateway_base}/heartbeat",
        },
    }

    results["handshake"] = handshake
    if heartbeat_payload is not None:
        results["heartbeat"] = {
            "payload": heartbeat_payload,
            "credential_expiry": heartbeat_expiry,
        }

    rotation_receipts: Dict[str, Any] = {}
    for connector_id in STAGE_B_TARGET_SERVICES:
        rotation_receipts[connector_id] = record_rotation_drill(
            connector_id,
            handshake=handshake,
        )
    results["rotation_ledger"] = rotation_receipts

    doctrine_ok, doctrine_failures = evaluate_operator_doctrine()
    results["doctrine_ok"] = doctrine_ok
    results["doctrine_failures"] = doctrine_failures

    return results


async def _async_main(args: argparse.Namespace) -> int:
    try:
        results = await run_stage_b_smoke(emit_heartbeat=not args.skip_heartbeat)
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("Stage B smoke checks failed: %s", exc)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("Stage B smoke checks completed.")
        print(json.dumps(results, indent=2, default=str))

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_async_main(args))


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
