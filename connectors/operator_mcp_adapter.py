"""MCP adapter shim for operator connectors."""

from __future__ import annotations

__version__ = "0.1.0"

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

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
    handshake: Mapping[str, Any] | None
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


def record_rotation_drill(
    connector_id: str,
    *,
    rotated_at: datetime | str | None = None,
    window_hours: int = ROTATION_WINDOW_HOURS,
    handshake: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a credential rotation drill entry for ``connector_id``."""

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


__all__ = [
    "OperatorMCPAdapter",
    "STAGE_B_TARGET_SERVICES",
    "ROTATION_WINDOW_HOURS",
    "record_rotation_drill",
    "load_rotation_history",
    "evaluate_operator_doctrine",
    "stage_b_context_enabled",
]
