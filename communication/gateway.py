"""Message gateway normalizing inputs from communication channels."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Protocol

from api import server as api_server


class authentication:
    """Shared authentication helpers for communication channels."""

    @staticmethod
    def verify_token(channel: str, token: str | None) -> None:
        """Validate ``token`` for ``channel``.

        The expected token is taken from the environment variable
        ``<CHANNEL>_TOKEN``. If no such variable is configured, verification is
        skipped. A mismatch raises :class:`PermissionError`.
        """

        expected = os.getenv(f"{channel.upper()}_TOKEN")
        if expected is None:
            return
        if token != expected:
            raise PermissionError(f"invalid token for {channel}")


@dataclass
class ChannelMessage:
    """Unified message format for all channels."""

    channel: str
    user_id: str
    content: str


class AICoreProtocol(Protocol):
    """Protocol representing the AI core interface."""

    async def handle_message(self, message: ChannelMessage) -> None:
        """Process an incoming ``ChannelMessage``."""
        ...


class Gateway:
    """Normalizes messages and routes them to the AI core."""

    def __init__(self, ai_core: AICoreProtocol) -> None:
        self.ai_core = ai_core

    async def handle_incoming(self, channel: str, user_id: str, content: str) -> None:
        """Create a ``ChannelMessage`` and forward it to the AI core."""
        if channel == "generate_video":
            await api_server.generate_video(content)
        elif channel == "stream_avatar":
            await api_server.broadcast_avatar_update(content)
        elif channel == "styles":
            await api_server.list_styles()
        message = ChannelMessage(channel=channel, user_id=user_id, content=content)
        await self.ai_core.handle_message(message)


__all__ = ["ChannelMessage", "Gateway", "authentication"]
