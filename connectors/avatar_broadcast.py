"""Broadcast avatar frames to Discord and Telegram.

- **Linked services:** Discord, Telegram
"""

from __future__ import annotations

__version__ = "0.1.0"

import asyncio
import contextlib
import logging
from typing import Any, Dict

from agents.event_bus import subscribe
from video_stream import session_manager
from tools import bot_discord, bot_telegram

logger = logging.getLogger(__name__)


async def broadcast(
    agent: str,
    *,
    discord_channel: int,
    telegram_chat: int,
    frame_limit: int | None = None,
) -> None:
    """Forward avatar frames and heartbeats to external services.

    Parameters
    ----------
    agent:
        Identifier of the avatar agent whose tracks are broadcast.
    discord_channel:
        Discord channel identifier used by :mod:`tools.bot_discord`.
    telegram_chat:
        Telegram chat identifier used by :mod:`tools.bot_telegram`.
    frame_limit:
        Optional limit to the number of frames broadcast. Primarily for tests;
        the function otherwise runs until the video track ends.
    """

    video, _ = session_manager.get_tracks(agent)
    if video is None:
        logger.warning("no video track for %s", agent)
        return

    heartbeat: Dict[str, Any] | None = None

    async def _handle(event: Any) -> None:
        nonlocal heartbeat
        if (
            getattr(event, "agent_id", None) == agent
            and getattr(event, "event_type", None) == "heartbeat"
        ):
            heartbeat = dict(getattr(event, "payload", {}))
            try:
                bot_discord.send_heartbeat(agent, heartbeat)
            except Exception:  # pragma: no cover - external dependency
                logger.exception("discord heartbeat forwarding failed")
            try:
                bot_telegram.send_heartbeat(telegram_chat, heartbeat)
            except Exception:  # pragma: no cover - external dependency
                logger.exception("telegram heartbeat forwarding failed")

    hb_task = asyncio.create_task(subscribe(_handle))

    sent = 0
    try:
        while True:
            try:
                frame = await video.recv()
            except Exception:
                break

            try:
                bot_discord.send_frame(frame, heartbeat)
            except Exception:  # pragma: no cover - external dependency
                logger.exception("discord frame forwarding failed")
            try:
                bot_telegram.send_frame(telegram_chat, frame, heartbeat)
            except Exception:  # pragma: no cover - external dependency
                logger.exception("telegram frame forwarding failed")

            sent += 1
            if frame_limit is not None and sent >= frame_limit:
                break
    finally:
        hb_task.cancel()
        with contextlib.suppress(Exception):
            await hb_task


__all__ = ["broadcast"]
