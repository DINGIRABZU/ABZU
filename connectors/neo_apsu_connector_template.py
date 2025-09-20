"""Neo-APSU connector template.

Demonstrates an MCP handshake, heartbeat emission, and doctrine compliance
checks for new connectors.
"""

from __future__ import annotations

__version__ = "0.2.0"

import asyncio
import json
import logging
import os
import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import httpx

LOGGER = logging.getLogger(__name__)

_USE_MCP = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")
_HANDSHAKE_ENDPOINT = "/handshake"
_STAGE_B_CONTEXT = "stage-b-rehearsal"

_DEFAULT_HEARTBEAT_CHAKRA = "neo"
_DEFAULT_HEARTBEAT_CYCLE_COUNT = 0

_ROOT = Path(__file__).resolve().parents[1]
_COMPONENT_INDEX = _ROOT / "component_index.json"
_CONNECTOR_INDEX = _ROOT / "docs" / "connectors" / "CONNECTOR_INDEX.md"

_DURATION_PATTERN = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


def _iso_now() -> str:
    """Return an ISO-8601 timestamp without microseconds."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_bool_env(name: str, default: bool = True) -> bool:
    """Interpret environment variable ``name`` as a boolean flag."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _build_handshake_payload() -> dict[str, Any]:
    """Assemble the capability payload for the MCP gateway handshake."""

    rotation_credentials: dict[str, Any] | None = None
    credential = os.getenv("MCP_CONNECTOR_TOKEN")
    if credential:
        rotation_credentials = {"type": "bearer", "token": credential}

    payload = {
        "identity": {
            "connector_id": os.getenv(
                "MCP_CONNECTOR_ID", "neo_apsu_connector_template"
            ),
            "version": __version__,
            "instance": os.getenv("MCP_CONNECTOR_INSTANCE", "local"),
        },
        "supported_contexts": _load_supported_contexts(),
        "rotation": {
            "last_rotated": os.getenv("MCP_LAST_ROTATED", _iso_now()),
            "rotation_window": os.getenv("MCP_ROTATION_WINDOW", "PT24H"),
            "supports_hot_swap": _load_bool_env("MCP_SUPPORTS_HOT_SWAP", True),
            "token_hint": os.getenv("MCP_ROTATION_HINT", "local"),
        },
    }
    if rotation_credentials:
        payload["rotation"]["credentials"] = rotation_credentials

    return payload


def _load_supported_contexts() -> list[dict[str, Any]]:
    """Read ``supported_contexts`` from env or provide defaults."""

    raw_contexts = os.getenv("MCP_SUPPORTED_CONTEXTS")
    if raw_contexts:
        try:
            contexts = json.loads(raw_contexts)
        except json.JSONDecodeError as exc:  # pragma: no cover - misconfiguration
            raise RuntimeError("Invalid MCP_SUPPORTED_CONTEXTS JSON") from exc
        if not isinstance(contexts, list):  # pragma: no cover - misconfiguration
            raise RuntimeError("MCP_SUPPORTED_CONTEXTS must be a list")
        return contexts

    return [
        {
            "name": _STAGE_B_CONTEXT,
            "channels": ["handshake", "heartbeat"],
            "capabilities": ["register", "telemetry"],
        }
    ]


def _context_name(context: Any) -> str | None:
    """Return the canonical name for ``context`` if available."""

    if isinstance(context, str):
        return context
    if isinstance(context, dict):
        name = context.get("name")
        if isinstance(name, str):
            return name
    return None


def _context_accepts_stage_b(contexts: Iterable[Any]) -> bool:
    """Check if ``contexts`` contains the Stage B rehearsal context."""

    for context in contexts:
        name = _context_name(context)
        if name != _STAGE_B_CONTEXT:
            continue
        if isinstance(context, dict):
            status = context.get("status", "accepted")
            if isinstance(status, str) and status.lower() in {"rejected", "deny"}:
                return False
        return True
    return False


def _sanitize_contexts(contexts: Iterable[Any]) -> list[str]:
    """Return sorted context names for logging."""

    names = {name for context in contexts if (name := _context_name(context))}
    return sorted(names)


def _normalize_isoformat(value: str) -> str:
    """Return ``value`` normalised as an ISO-8601 string with ``Z`` suffix."""

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("credential_expiry must be an ISO-8601 timestamp") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return parsed.isoformat().replace("+00:00", "Z")


def _normalize_credential_expiry(value: Any) -> str:
    """Normalise ``value`` to the canonical credential expiry representation."""

    if isinstance(value, datetime):
        value = value.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    if not isinstance(value, str):
        raise ValueError("credential_expiry must be an ISO-8601 timestamp")
    return _normalize_isoformat(value)


def _validate_chakra(value: Any) -> str:
    """Validate and return a chakra override."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError("chakra must be a non-empty string")
    return value.strip()


def _validate_cycle_count(value: Any) -> int:
    """Validate and return a cycle count override."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("cycle_count must be an integer")
    if value < 0:
        raise ValueError("cycle_count must be non-negative")
    return value


def _validate_context(value: Any) -> str:
    """Ensure heartbeat context aligns with Stage B expectations."""

    if not isinstance(value, str):
        raise ValueError("context must be a string")
    if value.strip() != _STAGE_B_CONTEXT:
        raise ValueError(f"context must be '{_STAGE_B_CONTEXT}'")
    return value.strip()


def _canonical_heartbeat_metadata(
    session: Mapping[str, Any] | None,
    *,
    credential_expiry: Any = None,
) -> dict[str, Any]:
    """Return the canonical metadata applied to all heartbeat payloads."""

    metadata = {
        "chakra": _DEFAULT_HEARTBEAT_CHAKRA,
        "cycle_count": _DEFAULT_HEARTBEAT_CYCLE_COUNT,
        "context": _STAGE_B_CONTEXT,
    }

    candidate = credential_expiry
    if candidate is None and session is not None:
        if not isinstance(session, Mapping):
            raise ValueError("session must be a mapping when supplied")
        candidate = session.get("credential_expiry") or session.get("expires_at")

    if candidate is not None:
        metadata["credential_expiry"] = _normalize_credential_expiry(candidate)

    return metadata


def _prepare_heartbeat_payload(
    payload: dict[str, Any],
    *,
    session: Mapping[str, Any] | None,
    credential_expiry: Any = None,
) -> dict[str, Any]:
    """Merge canonical metadata with ``payload`` and validate overrides."""

    if not isinstance(payload, dict):
        raise TypeError("heartbeat payload must be a dictionary")

    prepared: dict[str, Any] = dict(payload)
    defaults = _canonical_heartbeat_metadata(
        session, credential_expiry=credential_expiry
    )

    chakra = prepared.get("chakra", defaults["chakra"])
    prepared["chakra"] = _validate_chakra(chakra)

    cycle_count = prepared.get("cycle_count", defaults["cycle_count"])
    prepared["cycle_count"] = _validate_cycle_count(cycle_count)

    context = prepared.get("context", defaults["context"])
    prepared["context"] = _validate_context(context)

    expiry_value = prepared.get("credential_expiry")
    if expiry_value is None:
        expiry_value = defaults.get("credential_expiry")
    if expiry_value is None:
        raise ValueError(
            "heartbeat payload requires credential_expiry via session data or override"
        )
    prepared["credential_expiry"] = _normalize_credential_expiry(expiry_value)

    prepared.setdefault("emitted_at", _iso_now())

    return prepared


async def _post_handshake(
    client: httpx.AsyncClient, payload: dict[str, Any]
) -> httpx.Response:
    return await client.post(
        f"{_MCP_URL}{_HANDSHAKE_ENDPOINT}", json=payload, timeout=5.0
    )


async def handshake(
    client: httpx.AsyncClient | None = None, *, retries: int = 3
) -> dict[str, Any]:
    """Perform the initial MCP handshake with the gateway."""

    if not _USE_MCP:
        raise RuntimeError("MCP is not enabled")

    payload = _build_handshake_payload()
    attempt = 0
    backoff = 0.5
    last_exc: Exception | None = None

    async def _execute(session: httpx.AsyncClient) -> dict[str, Any]:
        nonlocal attempt, backoff, last_exc
        while attempt < retries:
            attempt += 1
            response = await _post_handshake(session, payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if response.status_code >= 500 and attempt < retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise

            data = response.json()
            if not isinstance(data, dict):
                raise RuntimeError("MCP handshake returned invalid payload")

            if not data.get("authenticated"):
                last_exc = RuntimeError("MCP handshake authentication failed")
                if attempt < retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise last_exc

            accepted_contexts = data.get("accepted_contexts", [])
            if not _context_accepts_stage_b(accepted_contexts):
                raise RuntimeError("Stage B rehearsal context not acknowledged by MCP")

            session_info = data.get("session")
            if not isinstance(session_info, dict) or "id" not in session_info:
                raise RuntimeError("MCP handshake missing session information")

            session_id = str(session_info["id"])
            LOGGER.info(
                "Stage B rehearsal handshake acknowledged",
                extra={
                    "event": "mcp.handshake",
                    "stage": "B",
                    "session_id": session_id,
                    "accepted_contexts": _sanitize_contexts(accepted_contexts),
                },
            )
            return data

        if last_exc is not None:  # pragma: no cover - defensive
            raise last_exc
        raise RuntimeError("MCP handshake exhausted retries without response")

    if client is not None:
        return await _execute(client)

    async with httpx.AsyncClient() as session:
        return await _execute(session)


async def send_heartbeat(
    payload: dict[str, Any],
    *,
    session: Mapping[str, Any] | None = None,
    credential_expiry: Any = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Emit heartbeat telemetry to maintain alignment."""

    if not _USE_MCP:
        raise RuntimeError("MCP is not enabled")

    body = _prepare_heartbeat_payload(
        payload, session=session, credential_expiry=credential_expiry
    )

    async def _execute(session_client: httpx.AsyncClient) -> None:
        resp = await session_client.post(
            f"{_MCP_URL}/heartbeat", json=body, timeout=5.0
        )
        resp.raise_for_status()

    if client is not None:
        await _execute(client)
        return

    async with httpx.AsyncClient() as session_client:
        await _execute(session_client)


def _parse_iso8601_timestamp(value: str) -> datetime:
    """Return ``value`` parsed as a timezone-aware UTC timestamp."""

    if not isinstance(value, str) or not value:
        raise ValueError("value must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError("value must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _parse_iso8601_duration(value: str) -> timedelta:
    """Return ``value`` parsed as a ``timedelta``."""

    if not isinstance(value, str) or not value:
        raise ValueError("rotation_window must be an ISO-8601 duration")
    match = _DURATION_PATTERN.match(value)
    if not match:
        raise ValueError(f"unsupported ISO-8601 duration: {value}")
    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def doctrine_compliant() -> tuple[bool, list[str]]:
    """Return compliance status and failure reasons for doctrine checks."""

    failures: list[str] = []

    registry_entry: dict[str, Any] | None = None
    try:
        registry_data = json.loads(_COMPONENT_INDEX.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"component registry missing: {_COMPONENT_INDEX}")
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        failures.append(f"component registry invalid JSON: {exc}")
    else:
        components = registry_data.get("components")
        if isinstance(components, list):
            for item in components:
                if (
                    isinstance(item, Mapping)
                    and item.get("path") == "connectors/neo_apsu_connector_template.py"
                ):
                    registry_entry = dict(item)
                    break
        if registry_entry is None:
            failures.append(
                "component registry missing neo_apsu_connector_template entry"
            )
        else:
            if registry_entry.get("id") != "neo_apsu_connector_template":
                failures.append(
                    "component registry id mismatch for neo_apsu_connector_template"
                )
            if registry_entry.get("version") != __version__:
                failures.append(
                    "component registry version mismatch for "
                    "neo_apsu_connector_template"
                )

    schema_path: Path | None = None
    try:
        connector_index_content = _CONNECTOR_INDEX.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"connector index missing: {_CONNECTOR_INDEX}")
        connector_index_content = ""

    registry_row: str | None = None
    for line in connector_index_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and "neo_apsu_connector_template" in stripped:
            registry_row = line
            break

    if registry_row is None:
        failures.append(
            "connector registry missing row for neo_apsu_connector_template"
        )
    else:
        columns = [col.strip() for col in registry_row.strip().split("|")[1:-1]]
        if len(columns) < 10:
            failures.append(
                "connector registry row malformed for neo_apsu_connector_template"
            )
        else:
            version_field = columns[2].strip("` ")
            if version_field:
                version_value = version_field.split()[0]
                if version_value != __version__:
                    failures.append(
                        "connector registry version mismatch for "
                        "neo_apsu_connector_template"
                    )
            schema_column = columns[9]
            match = re.search(r"\(([^)]+)\)", schema_column)
            if not match:
                failures.append(
                    "connector registry schema link missing for "
                    "neo_apsu_connector_template"
                )
            else:
                schema_rel = match.group(1)
                schema_path = (_CONNECTOR_INDEX.parent / Path(schema_rel)).resolve()
                if not schema_path.exists():
                    failures.append(f"schema reference not found: {schema_rel}")
                else:
                    try:
                        schema_data = json.loads(
                            schema_path.read_text(encoding="utf-8")
                        )
                    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                        failures.append(f"schema {schema_rel} invalid JSON: {exc}")
                    else:
                        required = schema_data.get("required", [])
                        expected = {
                            "chakra",
                            "cycle_count",
                            "context",
                            "credential_expiry",
                            "emitted_at",
                        }
                        missing = expected.difference(required)
                        if missing:
                            failures.append(
                                "schema missing required fields: "
                                + ", ".join(sorted(missing))
                            )
                        context_props = schema_data.get("properties", {}).get(
                            "context", {}
                        )
                        if context_props.get("const") != _STAGE_B_CONTEXT:
                            failures.append(
                                "schema context const does not enforce "
                                "stage-b-rehearsal"
                            )

    try:
        payload = _build_handshake_payload()
    except Exception as exc:  # pragma: no cover - defensive
        failures.append(f"failed to build handshake payload: {exc}")
    else:
        rotation = payload.get("rotation") or {}
        last_rotated_raw = rotation.get("last_rotated")
        if not last_rotated_raw:
            failures.append("rotation.last_rotated missing from handshake payload")
        else:
            try:
                last_rotated = _parse_iso8601_timestamp(last_rotated_raw)
            except ValueError as exc:
                failures.append(f"rotation.last_rotated invalid: {exc}")
            else:
                window_raw = rotation.get("rotation_window")
                if not window_raw:
                    failures.append(
                        "rotation.rotation_window missing from handshake payload"
                    )
                else:
                    try:
                        window_duration = _parse_iso8601_duration(window_raw)
                    except ValueError as exc:
                        failures.append(f"rotation_window invalid: {exc}")
                    else:
                        age = datetime.now(timezone.utc) - last_rotated
                        if age > window_duration:
                            overdue = age - window_duration
                            failures.append(f"credential rotation stale by {overdue}")
        supports_hot_swap = rotation.get("supports_hot_swap")
        if not isinstance(supports_hot_swap, bool):
            failures.append("rotation.supports_hot_swap must be a boolean")

    return (not failures, failures)


__all__ = ["handshake", "send_heartbeat", "doctrine_compliant"]
