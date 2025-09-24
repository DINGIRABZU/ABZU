"""MCP adapter shim for operator connectors."""

from __future__ import annotations

__version__ = "0.1.0"

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import httpx

from .base import ConnectorHeartbeat
from .neo_apsu_connector_template import (
    doctrine_compliant as template_doctrine,
    handshake as template_handshake,
    send_heartbeat as template_send_heartbeat,
)

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

        handshake_data = await template_handshake(self._client)
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
        await template_send_heartbeat(
            heartbeat_payload,
            session=self._session,
            credential_expiry=credential_expiry,
            client=self._client,
        )
        return heartbeat_payload

    def doctrine_report(self) -> tuple[bool, list[str]]:
        """Return doctrine compliance status for the operator MCP adoption."""

        return evaluate_operator_doctrine()


def record_rotation_drill(
    connector_id: str,
    *,
    rotated_at: datetime | None = None,
    window_hours: int = ROTATION_WINDOW_HOURS,
) -> dict[str, Any]:
    """Append a credential rotation drill entry for ``connector_id``."""

    timestamp = rotated_at or datetime.now(timezone.utc)
    entry = {
        "connector_id": connector_id,
        "rotated_at": _isoformat(timestamp),
        "window_hours": window_hours,
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

    template_ok, template_failures = template_doctrine()
    if not template_ok:
        failures.extend(template_failures)

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
