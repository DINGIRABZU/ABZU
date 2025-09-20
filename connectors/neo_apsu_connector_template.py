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
from datetime import datetime, timezone
from typing import Any, Iterable

import httpx

LOGGER = logging.getLogger(__name__)

_USE_MCP = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")
_HANDSHAKE_ENDPOINT = "/handshake"
_STAGE_B_CONTEXT = "stage-b-rehearsal"


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


async def send_heartbeat(payload: dict[str, Any]) -> None:
    """Emit heartbeat telemetry to maintain alignment."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{_MCP_URL}/heartbeat", json=payload, timeout=5.0)
        resp.raise_for_status()


def doctrine_compliant() -> bool:
    """Return True when the connector satisfies doctrine requirements."""
    # Insert doctrine verification logic here.
    return True


__all__ = ["handshake", "send_heartbeat", "doctrine_compliant"]
