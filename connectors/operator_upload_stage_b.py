"""Stage B MCP connector for the operator upload surface."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import httpx

from .neo_apsu_stage_b import StageBConnector, StageBConnectorConfig

__version__ = "0.1.0"

LOGGER = logging.getLogger(__name__)

_CONNECTOR = StageBConnector(
    StageBConnectorConfig(
        connector_id="operator_upload",
        registry_id="operator_upload_stage_b",
        module_path="connectors/operator_upload_stage_b.py",
        version=__version__,
        env_prefix="OPERATOR_UPLOAD_STAGE_B",
        supported_channels=("handshake", "heartbeat", "upload"),
        capabilities=("register", "telemetry", "upload"),
        chakra="operator",
        token_hint_default="operator-upload",
    ),
    logger=LOGGER,
)


async def handshake(
    client: httpx.AsyncClient | None = None, *, retries: int = 3
) -> dict[str, Any]:
    """Perform the Stage B handshake for the operator upload connector."""

    return await _CONNECTOR.handshake(client, retries=retries)


async def send_heartbeat(
    payload: dict[str, Any],
    *,
    session: Mapping[str, Any] | None = None,
    credential_expiry: Any = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Emit a Stage B heartbeat for the operator upload connector."""

    return await _CONNECTOR.send_heartbeat(
        payload,
        session=session,
        credential_expiry=credential_expiry,
        client=client,
    )


def doctrine_compliant() -> tuple[bool, list[str]]:
    """Return doctrine compliance status for the connector."""

    return _CONNECTOR.doctrine_compliant()


__all__ = ["handshake", "send_heartbeat", "doctrine_compliant"]
