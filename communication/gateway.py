from __future__ import annotations

"""Message gateway normalizing inputs from communication channels."""

from dataclasses import dataclass
from typing import Protocol


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
        message = ChannelMessage(channel=channel, user_id=user_id, content=content)
        await self.ai_core.handle_message(message)


__all__ = ["ChannelMessage", "Gateway"]
