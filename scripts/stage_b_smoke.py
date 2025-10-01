#!/usr/bin/env python3
"""Stage B rehearsal smoke checks for operator connectors."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

from scripts import _stage_runtime as stage_runtime

REPO_ROOT = stage_runtime.bootstrap(optional_modules=["neoabzu_memory"])

from connectors.operator_mcp_adapter import (
    ROTATION_WINDOW_HOURS,
    STAGE_B_TARGET_SERVICES,
    OperatorMCPAdapter,
    evaluate_operator_doctrine,
    load_latest_stage_c_handshake,
    normalize_handshake_for_trace,
    compute_handshake_checksum,
    record_rotation_drill,
    stage_b_context_enabled,
)
from connectors.operator_api_stage_b import (
    build_handshake_payload as build_operator_api_handshake,
)
from connectors.operator_upload_stage_b import (
    build_handshake_payload as build_operator_upload_handshake,
)
from connectors.crown_handshake_stage_b import (
    build_handshake_payload as build_crown_handshake,
)

LOGGER = logging.getLogger(__name__)
_STUB_ENV_FLAG = "ABZU_STAGE_B_SMOKE_STUB"

_CONNECTOR_HANDSHAKE_BUILDERS = {
    "operator_api": build_operator_api_handshake,
    "operator_upload": build_operator_upload_handshake,
    "crown_handshake": build_crown_handshake,
}


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


def _load_stage_c_handshake_artifact(
    metadata: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Return the Stage C handshake artifact for ``metadata``.

    The helper gracefully returns ``None`` when the metadata does not point to a
    readable JSON document on disk.
    """

    handshake_path = metadata.get("handshake_path")
    if not isinstance(handshake_path, str) or not handshake_path:
        return None

    try:
        path = Path(handshake_path)
    except (TypeError, ValueError):
        return None

    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _annotate_contexts(
    handshake: dict[str, Any] | None,
    metadata: Mapping[str, Any],
    *,
    accepted_via: str = "stage_c4_operator_mcp_drill",
) -> list[dict[str, Any]]:
    """Return accepted contexts annotated with Stage C evidence paths."""

    contexts = _normalize_contexts(
        handshake.get("accepted_contexts") if handshake else []
    )
    if not contexts:
        return []

    handshake_path = metadata.get("handshake_path")
    summary_path = metadata.get("summary_path")

    for entry in contexts:
        entry.setdefault("status", "accepted")
        if isinstance(handshake_path, str) and handshake_path:
            entry.setdefault("evidence_path", handshake_path)
        if isinstance(summary_path, str) and summary_path:
            entry.setdefault("summary_path", summary_path)
        entry.setdefault("accepted_via", accepted_via)

    if handshake is not None:
        handshake["accepted_contexts"] = list(contexts)

    return contexts


def _index_context_status(contexts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return a mapping of context name to metadata for ``contexts``."""

    indexed: dict[str, dict[str, Any]] = {}
    for entry in contexts:
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            continue
        details = {key: value for key, value in entry.items() if key != "name"}
        indexed[name] = details
    return indexed


def _merge_context_status(
    *candidates: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Return a merged context status mapping from ``candidates``."""

    merged: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        for name, details in candidate.items():
            if not isinstance(name, str):
                continue
            if isinstance(details, Mapping):
                merged[name] = {key: value for key, value in details.items()}
    return merged


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


def _synchronize_stage_c_handshake(
    handshake: dict[str, Any] | None,
    stage_c_handshake: dict[str, Any] | None,
) -> str | None:
    """Merge Stage C handshake metadata into the Stage B handshake payload.

    Returns the Stage C credential expiry when available so heartbeat payloads
    can mirror the drill metadata that triggered the promotion.
    """

    if not isinstance(handshake, dict) or not isinstance(stage_c_handshake, dict):
        return None

    credential_expiry: str | None = None

    stage_c_session = stage_c_handshake.get("session")
    if isinstance(stage_c_session, dict):
        session_section: dict[str, Any]
        if isinstance(handshake.get("session"), dict):
            session_section = dict(handshake["session"])
        else:
            session_section = {}
        for key, value in stage_c_session.items():
            if isinstance(key, str):
                session_section[key] = value
        handshake["session"] = session_section
        expiry_candidate = stage_c_session.get("credential_expiry")
        if isinstance(expiry_candidate, str) and expiry_candidate:
            credential_expiry = expiry_candidate

    stage_c_rotation = stage_c_handshake.get("rotation")
    if isinstance(stage_c_rotation, dict):
        handshake["rotation"] = dict(stage_c_rotation)

    stage_c_echo = stage_c_handshake.get("echo")
    if isinstance(stage_c_echo, dict):
        echo_section: dict[str, Any]
        if isinstance(handshake.get("echo"), dict):
            echo_section = dict(handshake["echo"])
        else:
            echo_section = {}
        rotation_echo = stage_c_echo.get("rotation")
        if isinstance(rotation_echo, dict):
            echo_section["rotation"] = dict(rotation_echo)
        handshake["echo"] = echo_section

    stage_c_contexts = _normalize_contexts(stage_c_handshake.get("accepted_contexts"))
    if stage_c_contexts:
        handshake["accepted_contexts"] = stage_c_contexts

    return credential_expiry


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


def _build_trace_bundle(
    connector_id: str,
    handshake: dict[str, Any] | None,
    *,
    gateway_base: str,
) -> dict[str, Any]:
    builder = _CONNECTOR_HANDSHAKE_BUILDERS.get(connector_id)
    request_payload: dict[str, Any] | None = None
    if callable(builder):
        try:
            request_payload = builder()
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.warning(
                "failed to build handshake payload for connector %s",
                connector_id,
                exc_info=True,
            )

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
            "stage": "B",
            "connector_id": connector_id,
            "contexts": contexts,
        },
        "response": {
            "message": f"trial handshake parity for {connector_id}",
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
    stage_c_artifact_handshake = _load_stage_c_handshake_artifact(stage_c_metadata)
    if stage_c_artifact_handshake:
        stage_c_handshake = stage_c_artifact_handshake
    if stage_c_handshake:
        stage_c_handshake = dict(stage_c_handshake)
    stage_c_contexts = _annotate_contexts(
        stage_c_handshake if stage_c_handshake else None,
        stage_c_metadata,
    )
    stage_c_context_status = _index_context_status(stage_c_contexts)
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

    stage_c_expiry = _synchronize_stage_c_handshake(handshake, stage_c_handshake)
    if stage_c_expiry:
        heartbeat_expiry = stage_c_expiry
        if heartbeat_payload is not None:
            heartbeat_payload["credential_expiry"] = stage_c_expiry
            heartbeat_session = heartbeat_payload.get("session")
            if isinstance(heartbeat_session, dict):
                heartbeat_session["credential_expiry"] = stage_c_expiry
            elif stage_c_handshake:
                heartbeat_payload["session"] = dict(
                    stage_c_handshake.get("session") or {}
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
    if promotion_metadata:
        results["context_promotions"] = promotion_metadata
    if heartbeat_payload is not None:
        results["heartbeat"] = {
            "payload": heartbeat_payload,
            "credential_expiry": heartbeat_expiry,
        }

    handshake_context_status = {}
    if isinstance(handshake, dict):
        handshake_context_status = _index_context_status(
            _normalize_contexts(handshake.get("accepted_contexts"))
        )

    rotation_receipts: Dict[str, Any] = {}
    trace_captures: Dict[str, Any] = {}
    for connector_id in STAGE_B_TARGET_SERVICES:
        overlay: Mapping[str, Mapping[str, Any]] | None = None
        if connector_id == "operator_api":
            overlay = (
                stage_c_context_status if stage_c_context_status else promotion_metadata
            )
        context_status = _merge_context_status(handshake_context_status, overlay)
        trace_bundle = _build_trace_bundle(
            connector_id,
            handshake if isinstance(handshake, dict) else None,
            gateway_base=gateway_base,
        )
        trace_captures[connector_id] = trace_bundle
        rotation_receipts[connector_id] = record_rotation_drill(
            connector_id,
            handshake=handshake,
            context_status=context_status or None,
            traces=trace_bundle,
        )
    results["rotation_ledger"] = rotation_receipts
    results["trial_traces"] = trace_captures

    doctrine_ok, doctrine_failures = evaluate_operator_doctrine()
    results["doctrine_ok"] = doctrine_ok
    results["doctrine_failures"] = doctrine_failures

    overrides = stage_runtime.get_sandbox_overrides()
    results["sandbox_overrides"] = overrides
    results["sandbox_summary"] = stage_runtime.format_sandbox_summary(
        "Stage B smoke runtime"
    )
    results["neoabzu_memory_stubbed"] = "neoabzu_memory" in overrides
    results["repo_root"] = str(REPO_ROOT)

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
