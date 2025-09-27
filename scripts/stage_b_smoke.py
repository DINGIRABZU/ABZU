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
    load_latest_stage_c_handshake,
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


def _normalize_contexts(value: Any) -> list[dict[str, Any]]:
    """Return ``value`` coerced to a list of context dictionaries."""

    contexts: list[dict[str, Any]] = []
    iterable: list[Any]
    if isinstance(value, list):
        iterable = value
    elif isinstance(value, tuple):
        iterable = list(value)
    else:
        iterable = []

    for entry in iterable:
        if isinstance(entry, dict):
            contexts.append(dict(entry))
        elif isinstance(entry, str):
            contexts.append({"name": entry, "status": "accepted"})

    return contexts


def _extract_stage_c_promotion(
    stage_c_handshake: dict[str, Any] | None,
    metadata: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return promotion metadata derived from the Stage C handshake."""

    if not isinstance(stage_c_handshake, dict):
        return {}

    contexts = _normalize_contexts(stage_c_handshake.get("accepted_contexts"))
    promotion: dict[str, dict[str, Any]] = {}
    for entry in contexts:
        if entry.get("name") != "stage-c-prep":
            continue
        status = entry.get("status")
        if not isinstance(status, str):
            continue
        if status.lower() != "accepted":
            continue

        promoted_at = None
        rotation = stage_c_handshake.get("rotation")
        if isinstance(rotation, dict):
            last_rotated = rotation.get("last_rotated")
            if isinstance(last_rotated, str) and last_rotated:
                promoted_at = last_rotated
        if promoted_at is None:
            completed_at = metadata.get("completed_at")
            if isinstance(completed_at, str) and completed_at:
                promoted_at = completed_at

        details: dict[str, Any] = {"status": status}
        if promoted_at:
            details["promoted_at"] = promoted_at
        handshake_path = metadata.get("handshake_path")
        if isinstance(handshake_path, str) and handshake_path:
            details["evidence_path"] = handshake_path
        summary_path = metadata.get("summary_path")
        if isinstance(summary_path, str) and summary_path:
            details["summary_path"] = summary_path

        promotion["stage-c-prep"] = details
        break

    return promotion


def _apply_promotion_to_handshake(
    handshake: dict[str, Any],
    promotion: dict[str, dict[str, Any]],
) -> None:
    if not promotion:
        return

    contexts = _normalize_contexts(handshake.get("accepted_contexts"))
    stage_c_entry = promotion.get("stage-c-prep")
    if stage_c_entry:
        found = False
        for context in contexts:
            if context.get("name") == "stage-c-prep":
                found = True
                status = stage_c_entry.get("status")
                if isinstance(status, str):
                    context["status"] = status
                promoted_at = stage_c_entry.get("promoted_at")
                if isinstance(promoted_at, str) and promoted_at:
                    context["promoted_at"] = promoted_at
                evidence_path = stage_c_entry.get("evidence_path")
                if isinstance(evidence_path, str) and evidence_path:
                    context["evidence_path"] = evidence_path
                summary_path = stage_c_entry.get("summary_path")
                if isinstance(summary_path, str) and summary_path:
                    context["summary_path"] = summary_path
                break
        if not found:
            new_entry = {"name": "stage-c-prep", **stage_c_entry}
            contexts.append(new_entry)

    handshake["accepted_contexts"] = contexts


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

    stage_c_handshake, stage_c_metadata = load_latest_stage_c_handshake()
    promotion_metadata = _extract_stage_c_promotion(
        dict(stage_c_handshake) if stage_c_handshake else None,
        stage_c_metadata,
    )
    if promotion_metadata:
        LOGGER.info(
            "Stage C drill promotion detected for Stage B contexts",
            extra={"promotion": promotion_metadata},
        )
        _apply_promotion_to_handshake(handshake, promotion_metadata)

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
    if promotion_metadata:
        results["context_promotions"] = promotion_metadata
    if heartbeat_payload is not None:
        results["heartbeat"] = {
            "payload": heartbeat_payload,
            "credential_expiry": heartbeat_expiry,
        }

    rotation_receipts: Dict[str, Any] = {}
    for connector_id in STAGE_B_TARGET_SERVICES:
        context_status = promotion_metadata if connector_id == "operator_api" else None
        rotation_receipts[connector_id] = record_rotation_drill(
            connector_id,
            handshake=handshake,
            context_status=context_status,
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
