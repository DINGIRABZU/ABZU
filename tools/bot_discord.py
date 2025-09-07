"""Discord bot that forwards messages to the `/glm-command` endpoint."""

from __future__ import annotations

__version__ = "0.1.0"

import asyncio
import logging
import os
from typing import Any

import requests

from connectors.signal_bus import publish, subscribe

logger = logging.getLogger(__name__)

_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
_GLM_URL = os.getenv("WEB_CONSOLE_API_URL", "http://localhost:8000/glm-command")

try:  # pragma: no cover - optional dependency
    import discord  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    discord = None  # type: ignore


def send_glm_command(text: str) -> str:
    """Return response from the GLM command endpoint."""
    res = requests.post(_GLM_URL, json={"command": text}, timeout=60)
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
        publish(
            "discord:in",
            {
                "channel": message.channel.id,
                "user": str(message.author.id),
                "content": message.content,
            },
        )
        reply = send_glm_command(message.content)
        await message.channel.send(reply)
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
            loop.create_task(channel.send(text))

    subscribe("discord:out", _outbound)

    return client


def main() -> None:
    """Run the Discord bot."""
    if _TOKEN is None:
        raise RuntimeError("DISCORD_BOT_TOKEN not configured")
    client = create_client()
    client.run(_TOKEN)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
