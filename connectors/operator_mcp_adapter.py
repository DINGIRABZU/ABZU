"""MCP adapter shim for operator connectors."""

from __future__ import annotations

__version__ = "0.1.0"

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from .base import ConnectorHeartbeat
from .crown_handshake_stage_b import doctrine_compliant as crown_doctrine
from .operator_api_stage_b import (
    doctrine_compliant as operator_api_doctrine,
    handshake as operator_api_handshake,
    send_heartbeat as operator_api_send_heartbeat,
)
from .operator_upload_stage_b import doctrine_compliant as operator_upload_doctrine

LOGGER = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]

STAGE_B_TARGET_SERVICES: tuple[str, ...] = (
    "operator_api",
    "operator_upload",
    "crown_handshake",
)
ROTATION_WINDOW_HOURS = 48
_ROTATION_LOG = _REPO_ROOT / "logs" / "stage_b_rotation_drills.jsonl"
_STAGE_C_ROOT = _REPO_ROOT / "logs" / "stage_c"
_STAGE_C_DRILL_STAGE = "stage_c4_operator_mcp_drill"

StageCHandshakeResult = tuple[Mapping[str, Any] | None, dict[str, str | None]]
_CONNECTOR_INDEX = _REPO_ROOT / "docs" / "connectors" / "CONNECTOR_INDEX.md"
_AUDIT_DOC = _REPO_ROOT / "docs" / "connectors" / "operator_mcp_audit.md"


def _isoformat(value: datetime) -> str:
    """Return ``value`` formatted as a UTC ISO-8601 string with ``Z`` suffix."""

    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


class OperatorMCPAdapter(ConnectorHeartbeat):
    """Adapter providing MCP handshake and heartbeat wrappers for operators."""

    def __init__(
        self,
        *,
        channel: str = "operator",
        heartbeat_interval: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(channel, interval=heartbeat_interval)
        self._client = client
        self._session: Mapping[str, Any] | None = None

    async def ensure_handshake(self) -> dict[str, Any]:
        """Perform the Stage B handshake and store the resulting session."""

        handshake_data = await operator_api_handshake(self._client)
        session_info = handshake_data.get("session")
        if isinstance(session_info, Mapping):
            self._session = session_info
        else:
            self._session = None
        LOGGER.debug("operator MCP handshake stored session=%s", self._session)
        return handshake_data

    async def emit_stage_b_heartbeat(
        self,
        payload: Mapping[str, Any] | None = None,
        *,
        credential_expiry: datetime | str | None = None,
    ) -> dict[str, Any]:
        """Emit a heartbeat with canonical Stage B metadata."""

        if self._session is None:
            handshake_data = await self.ensure_handshake()
            session_candidate = handshake_data.get("session")
            if isinstance(session_candidate, Mapping):
                self._session = session_candidate

        heartbeat_payload = dict(payload or {})
        await operator_api_send_heartbeat(
            heartbeat_payload,
            session=self._session,
            credential_expiry=credential_expiry,
            client=self._client,
        )
        return heartbeat_payload

    def doctrine_report(self) -> tuple[bool, list[str]]:
        """Return doctrine compliance status for the operator MCP adoption."""

        return evaluate_operator_doctrine()


def _parse_rotation_timestamp(value: Any) -> datetime | None:
    """Return ``value`` parsed as an aware UTC datetime when possible."""

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _extract_rotation_metadata(
    handshake: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Return rotation metadata contained within ``handshake``."""

    if not isinstance(handshake, Mapping):
        return {}
    rotation_section: Any = handshake.get("rotation")
    echo = handshake.get("echo")
    if isinstance(echo, Mapping) and not rotation_section:
        rotation_section = echo.get("rotation")
    return rotation_section if isinstance(rotation_section, Mapping) else {}


def _resolve_rotation_window(
    *,
    rotated_at: datetime,
    window_hours: int,
    duration_hint: str | None,
) -> dict[str, str]:
    """Return structured rotation window metadata for the ledger."""

    duration = duration_hint or f"PT{window_hours}H"
    expires_at = rotated_at + timedelta(hours=window_hours)
    window_id = f"{rotated_at.strftime('%Y%m%dT%H%M%SZ')}-{duration}"
    return {
        "window_id": window_id,
        "started_at": _isoformat(rotated_at),
        "expires_at": _isoformat(expires_at),
        "duration": duration,
    }


def _resolve_repo_path(value: Any) -> Path | None:
    """Return ``value`` as an absolute path when possible."""

    if not value:
        return None
    try:
        candidate = Path(str(value))
    except TypeError:
        return None
    if not candidate.is_absolute():
        candidate = (_REPO_ROOT / candidate).resolve()
    return candidate


def load_latest_stage_c_handshake() -> StageCHandshakeResult:
    """Return the latest successful Stage C MCP drill handshake and metadata."""

    handshake: Mapping[str, Any] | None = None
    metadata: dict[str, str | None] = {
        "summary_path": None,
        "handshake_path": None,
        "completed_at": None,
    }
    if not _STAGE_C_ROOT.exists():
        return handshake, metadata

    best_sort_key: tuple[int, datetime, str] | None = None
    for summary_path in sorted(_STAGE_C_ROOT.glob("*/summary.json")):
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if summary.get("stage") != _STAGE_C_DRILL_STAGE:
            continue
        if summary.get("status") != "success":
            continue

        completed_at_raw = summary.get("completed_at")
        completed_at = _parse_rotation_timestamp(completed_at_raw)
        artifacts = summary.get("artifacts")
        handshake_candidate: Mapping[str, Any] | None = None
        handshake_path: Path | None = None
        if isinstance(artifacts, Mapping):
            handshake_value = artifacts.get("mcp_handshake")
            handshake_path = _resolve_repo_path(handshake_value)
            if handshake_path and handshake_path.exists():
                try:
                    handshake_candidate = json.loads(
                        handshake_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError):
                    handshake_candidate = None

        if handshake_candidate is None:
            metrics = summary.get("metrics")
            if isinstance(metrics, Mapping):
                metrics_handshake = metrics.get("handshake")
                if isinstance(metrics_handshake, Mapping):
                    handshake_candidate = metrics_handshake

        if handshake_candidate is None:
            continue

        iso_completed: str | None = None
        if completed_at:
            iso_completed = _isoformat(completed_at)
        elif isinstance(completed_at_raw, str):
            try:
                fallback_dt = datetime.fromisoformat(
                    completed_at_raw.replace("Z", "+00:00")
                )
            except ValueError:
                fallback_dt = None
            if fallback_dt is not None:
                if fallback_dt.tzinfo is None:
                    fallback_dt = fallback_dt.replace(tzinfo=timezone.utc)
                iso_completed = _isoformat(fallback_dt)

        candidate_key = (
            1 if completed_at else 0,
            completed_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
            summary_path.name,
        )
        if best_sort_key is None or candidate_key > best_sort_key:
            handshake = handshake_candidate
            metadata = {
                "summary_path": str(summary_path),
                "handshake_path": str(handshake_path) if handshake_path else None,
                "completed_at": iso_completed,
            }
            best_sort_key = candidate_key

    return handshake, metadata


def record_rotation_drill(
    connector_id: str,
    *,
    rotated_at: datetime | str | None = None,
    window_hours: int = ROTATION_WINDOW_HOURS,
    handshake: Mapping[str, Any] | None = None,
    context_status: Mapping[str, Mapping[str, Any]] | None = None,
    traces: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a credential rotation drill entry for ``connector_id``.

    ``context_status`` can embed downstream promotion metadata (for example,
    Stage C adoption evidence) that should travel with the ledger entry.
    """

    rotation_metadata = _extract_rotation_metadata(handshake)
    rotation_timestamp = _parse_rotation_timestamp(
        rotated_at if rotated_at is not None else rotation_metadata.get("last_rotated")
    )
    timestamp = rotation_timestamp or datetime.now(timezone.utc)

    duration_hint: str | None = None
    rotation_window_raw = rotation_metadata.get("rotation_window")
    if isinstance(rotation_window_raw, str):
        duration_hint = rotation_window_raw

    entry = {
        "connector_id": connector_id,
        "rotated_at": _isoformat(timestamp),
        "window_hours": window_hours,
        "rotation_window": _resolve_rotation_window(
            rotated_at=timestamp,
            window_hours=window_hours,
            duration_hint=duration_hint,
        ),
    }
    if context_status:
        entry["context_status"] = {
            key: dict(value)
            for key, value in context_status.items()
            if isinstance(key, str) and isinstance(value, Mapping)
        }

    if traces:
        entry["traces"] = _coerce_trace_payload(traces)

    _ROTATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _ROTATION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    LOGGER.info("Recorded Stage B rotation drill", extra=entry)
    return entry


def load_rotation_history() -> list[dict[str, Any]]:
    """Return recorded rotation drills."""

    if not _ROTATION_LOG.exists():
        return []
    return [
        json.loads(line)
        for line in _ROTATION_LOG.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evaluate_operator_doctrine() -> tuple[bool, list[str]]:
    """Validate doctrine requirements tied to the operator MCP migration."""

    failures: list[str] = []

    audit_exists = _AUDIT_DOC.exists()
    if not audit_exists:
        failures.append(f"audit document missing: {_AUDIT_DOC}")

    try:
        connector_index = _CONNECTOR_INDEX.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"connector index missing: {_CONNECTOR_INDEX}")
        connector_index = ""

    if "operator_mcp_audit.md" not in connector_index:
        failures.append("connector index not referencing MCP audit")
    if "MCP adapter stub" not in connector_index:
        failures.append("connector index missing MCP adapter status note")

    rotation_entries = load_rotation_history()
    if not rotation_entries:
        failures.append("no credential rotation drills recorded")
    else:
        latest = rotation_entries[-1]
        if latest.get("window_hours") != ROTATION_WINDOW_HOURS:
            failures.append("latest rotation drill does not confirm 48-hour window")
        rotation_window = latest.get("rotation_window")
        if not isinstance(rotation_window, Mapping):
            failures.append("latest rotation drill missing rotation_window metadata")
        else:
            for field in ("window_id", "started_at", "expires_at", "duration"):
                if field not in rotation_window:
                    failures.append(f"rotation_window missing field: {field}")

    for name, doctrine_check in (
        ("operator_api_stage_b", operator_api_doctrine),
        ("operator_upload_stage_b", operator_upload_doctrine),
        ("crown_handshake_stage_b", crown_doctrine),
    ):
        ok, issues = doctrine_check()
        if not ok:
            failures.extend(f"{name}: {issue}" for issue in issues)

    return (not failures, failures)


def stage_b_context_enabled() -> bool:
    """Return True when MCP toggles indicate Stage B rehearsals are active."""

    return os.getenv("ABZU_USE_MCP") == "1"


def _coerce_trace_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``value`` coerced to a JSON-serialisable mapping."""

    def _convert(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): _convert(val)
                for key, val in item.items()
                if isinstance(key, str)
            }
        if isinstance(item, (list, tuple, set)):
            return [_convert(element) for element in item]
        return item

    return _convert(value)


def normalize_handshake_for_trace(
    handshake: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return ``handshake`` normalised for REST↔gRPC parity checks."""

    if not isinstance(handshake, Mapping):
        return {}

    normalized: dict[str, Any] = {}

    authenticated = handshake.get("authenticated")
    if isinstance(authenticated, bool):
        normalized["authenticated"] = authenticated

    session = handshake.get("session")
    if isinstance(session, Mapping):
        session_view: dict[str, Any] = {}
        for key in ("id", "credential_expiry", "issued_at"):
            value = session.get(key)
            if value is not None:
                session_view[key] = value
        if session_view:
            normalized["session"] = session_view

    contexts = handshake.get("accepted_contexts")
    context_entries: list[dict[str, Any]] = []
    if isinstance(contexts, Sequence):
        for raw in contexts:
            if isinstance(raw, Mapping):
                entry: dict[str, Any] = {}
                for key in (
                    "name",
                    "status",
                    "promoted_at",
                    "evidence_path",
                    "summary_path",
                ):
                    value = raw.get(key)
                    if value is not None:
                        entry[key] = value
                if entry:
                    context_entries.append(entry)
            elif isinstance(raw, str):
                context_entries.append({"name": raw, "status": "accepted"})
    if context_entries:
        context_entries.sort(key=lambda item: item.get("name", ""))
        normalized["accepted_contexts"] = context_entries

    rotation = _extract_rotation_metadata(handshake)
    if rotation:
        rotation_view: dict[str, Any] = {}
        for key in ("connector_id", "last_rotated", "rotation_window", "window_id"):
            value = rotation.get(key)
            if value is not None:
                rotation_view[key] = value
        if rotation_view:
            normalized["rotation"] = rotation_view

    echo = handshake.get("echo")
    if isinstance(echo, Mapping):
        echo_view: dict[str, Any] = {}
        rotation_echo = echo.get("rotation")
        if isinstance(rotation_echo, Mapping):
            echo_rotation: dict[str, Any] = {}
            for key in ("connector_id", "last_rotated", "rotation_window", "window_id"):
                value = rotation_echo.get(key)
                if value is not None:
                    echo_rotation[key] = value
            if echo_rotation:
                echo_view["rotation"] = echo_rotation
        if echo_view:
            normalized["echo"] = echo_view

    return normalized


def compute_handshake_checksum(handshake: Mapping[str, Any] | None) -> str | None:
    """Return a SHA-256 checksum for ``handshake`` after normalisation."""

    normalized = normalize_handshake_for_trace(handshake)
    if not normalized:
        return None
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def latest_rotation_entry(connector_id: str) -> Mapping[str, Any] | None:
    """Return the most recent rotation ledger entry for ``connector_id``."""

    history = load_rotation_history()
    for entry in reversed(history):
        if entry.get("connector_id") == connector_id:
            return entry
    return None


__all__ = [
    "OperatorMCPAdapter",
    "STAGE_B_TARGET_SERVICES",
    "ROTATION_WINDOW_HOURS",
    "record_rotation_drill",
    "load_rotation_history",
    "load_latest_stage_c_handshake",
    "evaluate_operator_doctrine",
    "stage_b_context_enabled",
    "normalize_handshake_for_trace",
    "compute_handshake_checksum",
    "latest_rotation_entry",
]
