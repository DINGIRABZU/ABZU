"""Discord bot that forwards messages and emits heartbeats."""

from __future__ import annotations

__version__ = "0.3.0"

import asyncio
import logging
import os
from typing import Any

import requests

import connectors.signal_bus as signal_bus
from connectors.base import ConnectorHeartbeat
from connectors.message_formatter import format_message

logger = logging.getLogger(__name__)

_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
_GLM_URL = os.getenv("WEB_CONSOLE_API_URL", "http://localhost:8000/glm-command")
_USE_MCP = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")
# Discord's messaging API remains external; MCP only routes internal commands.

try:  # pragma: no cover - optional dependency
    import discord  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    discord = None  # type: ignore


def send_glm_command(text: str) -> str:
    """Return GLM response via MCP when enabled, otherwise via HTTP."""
    if _USE_MCP:
        url = f"{_MCP_URL}/model/invoke"
        payload = {"model": "glm", "text": text}
    else:
        url = _GLM_URL
        payload = {"command": text}
    res = requests.post(url, json=payload, timeout=60)
    res.raise_for_status()
    return res.json().get("result", "")


def create_client() -> Any:
    """Return a configured Discord client instance."""
    if discord is None:
        raise RuntimeError("discord.py not installed")

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    loop = asyncio.get_event_loop()

    @client.event  # type: ignore[misc]
    async def on_message(message: discord.Message) -> None:  # pragma: no cover
        if message.author.bot:
            return
        signal_bus.publish(
            "discord:in",
            {
                "channel": message.channel.id,
                "user": str(message.author.id),
                "content": message.content,
            },
        )
        reply = send_glm_command(message.content)
        await message.channel.send(format_message("discord", reply))
        try:
            from core import expressive_output

            path = expressive_output.speak(reply, "neutral")
            await message.channel.send(file=discord.File(path))
        except Exception:
            logger.exception("Failed synthesizing voice")

    def _outbound(payload: dict) -> None:
        channel_id = payload.get("channel")
        text = payload.get("content", "")
        channel = client.get_channel(int(channel_id)) if channel_id else None
        if channel:
            loop.create_task(channel.send(format_message("discord", text)))

    signal_bus.subscribe("discord:out", _outbound)

    return client


class DiscordConnector(ConnectorHeartbeat):
    """Discord connector emitting heartbeats."""

    def __init__(
        self, token: str, *, interval: float = 30.0, miss_threshold: int = 3
    ) -> None:
        super().__init__("discord", interval=interval, miss_threshold=miss_threshold)
        self._token = token
        self._client = create_client()

    def run(self) -> None:
        self.start()
        self._client.run(self._token)


def main() -> None:
    """Run the Discord bot."""
    if _TOKEN is None:
        raise RuntimeError("DISCORD_BOT_TOKEN not configured")
    DiscordConnector(_TOKEN).run()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
