"""Shared Neo-APSU Stage B connector helpers.

Provides reusable handshake, heartbeat, and doctrine compliance utilities
for connectors that interact with the MCP gateway during Stage B rehearsals.
"""

from __future__ import annotations

__version__ = "0.1.0"

from dataclasses import dataclass
import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import httpx

__all__ = [
    "StageBConnectorConfig",
    "StageBConnector",
]


_MCP_ENABLED = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")
_HANDSHAKE_ENDPOINT = "/handshake"
_HEARTBEAT_ENDPOINT = "/heartbeat"
_STAGE_B_CONTEXT = "stage-b-rehearsal"

_ROOT = Path(__file__).resolve().parents[1]
_COMPONENT_INDEX = _ROOT / "component_index.json"
_CONNECTOR_INDEX = _ROOT / "docs" / "connectors" / "CONNECTOR_INDEX.md"
_SCHEMA_DIR = _ROOT / "schemas"

_SCHEMA_FIELDS = {
    "chakra",
    "cycle_count",
    "context",
    "credential_expiry",
    "emitted_at",
}


@dataclass(frozen=True)
class StageBConnectorConfig:
    """Configuration describing a Stage B connector."""

    connector_id: str
    registry_id: str
    module_path: str
    version: str
    env_prefix: str
    default_instance: str = "local"
    supported_channels: Sequence[str] = ("handshake", "heartbeat")
    capabilities: Sequence[str] = ("register", "telemetry")
    chakra: str = "neo"
    cycle_count: int = 0
    context_name: str = _STAGE_B_CONTEXT
    rotation_window_default: str = "PT48H"
    token_hint_default: str = "stage-b"
    schema_relpath: str = "../../schemas/mcp_heartbeat_payload.schema.json"
    docs_row_hint: str | None = None

    def env_name(self, suffix: str) -> str:
        """Return the environment variable name using ``env_prefix``."""

        return f"{self.env_prefix}_{suffix}"

    @property
    def docs_identifier(self) -> str:
        """Identifier used when scanning connector documentation rows."""

        return self.docs_row_hint or self.registry_id


def _iso_now() -> str:
    """Return the current UTC time without microseconds."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_bool_env(name: str, default: bool) -> bool:
    """Interpret environment variable ``name`` as a boolean flag."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _context_name(context: Any) -> str | None:
    """Return the context name from ``context`` if present."""

    if isinstance(context, str):
        return context
    if isinstance(context, Mapping):
        name = context.get("name")
        if isinstance(name, str):
            return name
    return None


def _context_accepts_stage_b(contexts: Iterable[Any], stage_context: str) -> bool:
    """Return ``True`` if ``contexts`` accepts the Stage B rehearsal context."""

    for context in contexts:
        name = _context_name(context)
        if name != stage_context:
            continue
        if isinstance(context, Mapping):
            status = context.get("status", "accepted")
            if isinstance(status, str) and status.lower() in {"rejected", "deny"}:
                return False
        return True
    return False


def _sanitize_contexts(contexts: Iterable[Any]) -> list[str]:
    """Return sorted list of context names for logging."""

    names = {name for context in contexts if (name := _context_name(context))}
    return sorted(names)


def _normalize_isoformat(value: str) -> str:
    """Normalise ``value`` to an ISO-8601 string with ``Z`` suffix."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return parsed.isoformat().replace("+00:00", "Z")


def _parse_iso8601_timestamp(value: str) -> datetime:
    """Parse ``value`` as an aware UTC datetime."""

    if not isinstance(value, str) or not value:
        raise ValueError("value must be an ISO-8601 timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _parse_iso8601_duration(value: str) -> timedelta:
    """Parse ``value`` as an ISO-8601 duration string."""

    pattern = re.compile(
        r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
    )
    if not isinstance(value, str) or not value:
        raise ValueError("rotation_window must be an ISO-8601 duration")
    match = pattern.match(value)
    if not match:
        raise ValueError(f"unsupported ISO-8601 duration: {value}")
    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


class StageBConnector:
    """Utility implementing Stage B MCP flows for a connector."""

    def __init__(
        self,
        config: StageBConnectorConfig,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Handshake helpers
    # ------------------------------------------------------------------

    def _load_supported_contexts(self) -> list[dict[str, Any]]:
        """Return supported contexts, allowing overrides via environment."""

        env_name = self._config.env_name("SUPPORTED_CONTEXTS")
        raw_contexts = os.getenv(env_name)
        if raw_contexts:
            try:
                contexts = json.loads(raw_contexts)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON supplied via {env_name}") from exc
            if not isinstance(contexts, list):
                raise RuntimeError(f"{env_name} must be a JSON list")
            return contexts

        return [
            {
                "name": self._config.context_name,
                "channels": list(self._config.supported_channels),
                "capabilities": list(self._config.capabilities),
            }
        ]

    def build_handshake_payload(self) -> dict[str, Any]:
        """Construct the Stage B handshake payload for the connector."""

        credential = os.getenv(self._config.env_name("CONNECTOR_TOKEN"))
        rotation_credentials: dict[str, Any] | None
        if credential:
            rotation_credentials = {"type": "bearer", "token": credential}
        else:
            rotation_credentials = None

        payload = {
            "identity": {
                "connector_id": os.getenv(
                    self._config.env_name("CONNECTOR_ID"), self._config.connector_id
                ),
                "version": self._config.version,
                "instance": os.getenv(
                    self._config.env_name("CONNECTOR_INSTANCE"),
                    self._config.default_instance,
                ),
            },
            "supported_contexts": self._load_supported_contexts(),
            "rotation": {
                "last_rotated": os.getenv(
                    self._config.env_name("LAST_ROTATED"), _iso_now()
                ),
                "rotation_window": os.getenv(
                    self._config.env_name("ROTATION_WINDOW"),
                    self._config.rotation_window_default,
                ),
                "supports_hot_swap": _load_bool_env(
                    self._config.env_name("SUPPORTS_HOT_SWAP"), True
                ),
                "token_hint": os.getenv(
                    self._config.env_name("ROTATION_HINT"),
                    self._config.token_hint_default,
                ),
            },
        }
        if rotation_credentials:
            payload["rotation"]["credentials"] = rotation_credentials
        return payload

    async def handshake(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        retries: int = 3,
    ) -> dict[str, Any]:
        """Perform the MCP handshake for this connector."""

        if not _MCP_ENABLED:
            raise RuntimeError("MCP is not enabled")

        payload = self.build_handshake_payload()
        attempt = 0
        backoff = 0.5
        last_exc: Exception | None = None

        async def _execute(session: httpx.AsyncClient) -> dict[str, Any]:
            nonlocal attempt, backoff, last_exc
            while attempt < retries:
                attempt += 1
                response = await session.post(
                    f"{_MCP_URL}{_HANDSHAKE_ENDPOINT}",
                    json=payload,
                    timeout=5.0,
                )
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
                if not _context_accepts_stage_b(
                    accepted_contexts, self._config.context_name
                ):
                    raise RuntimeError(
                        "Stage B rehearsal context not acknowledged by MCP"
                    )

                session_info = data.get("session")
                if not isinstance(session_info, Mapping) or "id" not in session_info:
                    raise RuntimeError("MCP handshake missing session information")

                session_id = str(session_info["id"])
                self._logger.info(
                    "Stage B rehearsal handshake acknowledged",
                    extra={
                        "event": "mcp.handshake",
                        "stage": "B",
                        "session_id": session_id,
                        "connector_id": self._config.connector_id,
                        "accepted_contexts": _sanitize_contexts(accepted_contexts),
                    },
                )
                return data

            if last_exc is not None:
                raise last_exc
            raise RuntimeError("MCP handshake exhausted retries without response")

        if client is not None:
            return await _execute(client)

        async with httpx.AsyncClient() as session:
            return await _execute(session)

    # ------------------------------------------------------------------
    # Heartbeat helpers
    # ------------------------------------------------------------------

    def _canonical_heartbeat_metadata(
        self,
        session: Mapping[str, Any] | None,
        *,
        credential_expiry: Any = None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "chakra": self._config.chakra,
            "cycle_count": self._config.cycle_count,
            "context": self._config.context_name,
        }

        candidate = credential_expiry
        if candidate is None and session is not None:
            if not isinstance(session, Mapping):
                raise ValueError("session must be a mapping when supplied")
            candidate = session.get("credential_expiry") or session.get("expires_at")

        if candidate is not None:
            metadata["credential_expiry"] = _normalize_isoformat(str(candidate))

        return metadata

    def _prepare_heartbeat_payload(
        self,
        payload: dict[str, Any],
        *,
        session: Mapping[str, Any] | None,
        credential_expiry: Any = None,
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("heartbeat payload must be a dictionary")

        prepared = dict(payload)
        defaults = self._canonical_heartbeat_metadata(
            session, credential_expiry=credential_expiry
        )

        chakra = prepared.get("chakra", defaults.get("chakra"))
        if not isinstance(chakra, str) or not chakra.strip():
            raise ValueError("chakra must be a non-empty string")
        prepared["chakra"] = chakra.strip()

        cycle_count = prepared.get("cycle_count", defaults.get("cycle_count"))
        if isinstance(cycle_count, bool) or not isinstance(cycle_count, int):
            raise ValueError("cycle_count must be an integer")
        if cycle_count < 0:
            raise ValueError("cycle_count must be non-negative")
        prepared["cycle_count"] = cycle_count

        context = prepared.get("context", defaults.get("context"))
        if not isinstance(context, str):
            raise ValueError("context must be a string")
        context_value = context.strip()
        if context_value != self._config.context_name:
            raise ValueError(f"context must be '{self._config.context_name}'")
        prepared["context"] = context_value

        expiry_value = prepared.get("credential_expiry")
        if expiry_value is None:
            expiry_value = defaults.get("credential_expiry")
        if expiry_value is None:
            raise ValueError(
                "heartbeat payload requires credential_expiry via session data "
                "or override"
            )
        prepared["credential_expiry"] = _normalize_isoformat(str(expiry_value))

        prepared.setdefault("emitted_at", _iso_now())
        return prepared

    def build_heartbeat_payload(
        self,
        payload: dict[str, Any],
        *,
        session: Mapping[str, Any] | None = None,
        credential_expiry: Any = None,
    ) -> dict[str, Any]:
        """Return the canonical heartbeat payload without transmitting it."""

        return self._prepare_heartbeat_payload(
            payload, session=session, credential_expiry=credential_expiry
        )

    async def send_heartbeat(
        self,
        payload: dict[str, Any],
        *,
        session: Mapping[str, Any] | None = None,
        credential_expiry: Any = None,
        client: httpx.AsyncClient | None = None,
    ) -> dict[str, Any]:
        """Send the Stage B heartbeat payload to the MCP gateway."""

        if not _MCP_ENABLED:
            raise RuntimeError("MCP is not enabled")

        body = self.build_heartbeat_payload(
            payload, session=session, credential_expiry=credential_expiry
        )

        async def _execute(session_client: httpx.AsyncClient) -> None:
            response = await session_client.post(
                f"{_MCP_URL}{_HEARTBEAT_ENDPOINT}",
                json=body,
                timeout=5.0,
            )
            response.raise_for_status()

        if client is not None:
            await _execute(client)
            return body

        async with httpx.AsyncClient() as session_client:
            await _execute(session_client)
        return body

    # ------------------------------------------------------------------
    # Doctrine compliance
    # ------------------------------------------------------------------

    def doctrine_compliant(self) -> tuple[bool, list[str]]:
        """Evaluate connector doctrine compliance."""

        failures: list[str] = []

        registry_entry: Mapping[str, Any] | None = None
        try:
            registry_data = json.loads(_COMPONENT_INDEX.read_text(encoding="utf-8"))
        except FileNotFoundError:
            failures.append(f"component registry missing: {_COMPONENT_INDEX}")
        except json.JSONDecodeError as exc:
            failures.append(f"component registry invalid JSON: {exc}")
        else:
            components = registry_data.get("components")
            if isinstance(components, list):
                for item in components:
                    if (
                        isinstance(item, Mapping)
                        and item.get("path") == self._config.module_path
                    ):
                        registry_entry = item
                        break
            if registry_entry is None:
                failures.append(
                    f"component registry missing entry for {self._config.registry_id}"
                )
            else:
                if registry_entry.get("id") != self._config.registry_id:
                    failures.append(
                        f"component registry id mismatch for {self._config.registry_id}"
                    )
                if registry_entry.get("version") != self._config.version:
                    failures.append(
                        "component registry version mismatch for "
                        f"{self._config.registry_id}"
                    )

        schema_path: Path | None = None
        try:
            connector_index_content = _CONNECTOR_INDEX.read_text(encoding="utf-8")
        except FileNotFoundError:
            failures.append(f"connector index missing: {_CONNECTOR_INDEX}")
            connector_index_content = ""

        registry_row: str | None = None
        identifier = f"`{self._config.registry_id}`"
        for line in connector_index_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and identifier in stripped:
                registry_row = line
                break

        if registry_row is None:
            failures.append(
                f"connector registry missing row for {self._config.registry_id}"
            )
        else:
            columns = [col.strip() for col in registry_row.strip().split("|")[1:-1]]
            if len(columns) < 10:
                failures.append(
                    f"connector registry row malformed for {self._config.registry_id}"
                )
            else:
                version_field = columns[2].strip("` ")
                if version_field:
                    version_value = version_field.split()[0]
                    if version_value != self._config.version:
                        failures.append(
                            "connector registry version mismatch for "
                            f"{self._config.registry_id}"
                        )
                schema_column = columns[9]
                match = re.search(r"\(([^)]+)\)", schema_column)
                if not match:
                    failures.append(
                        "connector registry schema link missing for "
                        f"{self._config.registry_id}"
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
                        except json.JSONDecodeError as exc:
                            failures.append(f"schema {schema_rel} invalid JSON: {exc}")
                        else:
                            required = schema_data.get("required", [])
                            missing = _SCHEMA_FIELDS.difference(required)
                            if missing:
                                failures.append(
                                    "schema missing required fields: "
                                    + ", ".join(sorted(missing))
                                )
                            context_props = schema_data.get("properties", {}).get(
                                "context", {}
                            )
                            if context_props.get("const") != self._config.context_name:
                                failures.append(
                                    "schema context const does not enforce "
                                    f"{self._config.context_name}"
                                )

        try:
            payload = self.build_handshake_payload()
        except Exception as exc:
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
                                failures.append(
                                    f"credential rotation stale by {overdue}"
                                )
            supports_hot_swap = rotation.get("supports_hot_swap")
            if not isinstance(supports_hot_swap, bool):
                failures.append("rotation.supports_hot_swap must be a boolean")

        return (not failures, failures)
