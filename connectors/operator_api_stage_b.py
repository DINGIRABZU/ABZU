"""Stage B MCP connector for the operator command surface."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import httpx

from .neo_apsu_stage_b import StageBConnector, StageBConnectorConfig

__version__ = "0.1.0"

LOGGER = logging.getLogger(__name__)

_CONNECTOR = StageBConnector(
    StageBConnectorConfig(
        connector_id="operator_api",
        registry_id="operator_api_stage_b",
        module_path="connectors/operator_api_stage_b.py",
        version=__version__,
        env_prefix="OPERATOR_API_STAGE_B",
        supported_channels=("handshake", "heartbeat", "command"),
        capabilities=("register", "telemetry", "command"),
        chakra="operator",
        token_hint_default="operator",
    ),
    logger=LOGGER,
)


async def handshake(
    client: httpx.AsyncClient | None = None, *, retries: int = 3
) -> dict[str, Any]:
    """Perform the Stage B handshake for the operator command connector."""

    return await _CONNECTOR.handshake(client, retries=retries)


def build_handshake_payload() -> dict[str, Any]:
    """Return the Stage B handshake payload for rehearsal logging."""

    return _CONNECTOR.build_handshake_payload()


async def send_heartbeat(
    payload: dict[str, Any],
    *,
    session: Mapping[str, Any] | None = None,
    credential_expiry: Any = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Emit a Stage B heartbeat for the operator command connector."""

    return await _CONNECTOR.send_heartbeat(
        payload,
        session=session,
        credential_expiry=credential_expiry,
        client=client,
    )


def build_heartbeat_payload(
    payload: dict[str, Any],
    *,
    session: Mapping[str, Any] | None = None,
    credential_expiry: Any = None,
) -> dict[str, Any]:
    """Return the prepared Stage B heartbeat payload without sending it."""

    return _CONNECTOR.build_heartbeat_payload(
        payload,
        session=session,
        credential_expiry=credential_expiry,
    )


def doctrine_compliant() -> tuple[bool, list[str]]:
    """Return doctrine compliance status for the connector."""

    return _CONNECTOR.doctrine_compliant()


__all__ = [
    "handshake",
    "send_heartbeat",
    "doctrine_compliant",
    "build_handshake_payload",
    "build_heartbeat_payload",
]
