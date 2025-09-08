"""Telegram bot forwarding messages and emitting heartbeats."""

from __future__ import annotations

__version__ = "0.3.0"

import logging
import os
import time
from pathlib import Path

import requests

import connectors.signal_bus as signal_bus
from connectors.base import ConnectorHeartbeat
from connectors.message_formatter import format_message

logger = logging.getLogger(__name__)

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_API = f"https://api.telegram.org/bot{_TOKEN}" if _TOKEN else None
_GLM_URL = os.getenv("WEB_CONSOLE_API_URL", "http://localhost:8000/glm-command")
_USE_MCP = os.getenv("ABZU_USE_MCP") == "1"
_MCP_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")
# Telegram's messaging API remains external; MCP only routes internal commands.


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


def send_message(chat_id: int, text: str) -> None:
    """Send ``text`` to ``chat_id`` via Telegram."""
    if not _API:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
    payload = format_message("telegram", text)
    requests.post(f"{_API}/sendMessage", json={"chat_id": chat_id, "text": payload})


def send_voice(chat_id: int, path: Path) -> None:
    """Send ``path`` as a voice message."""
    if not _API:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
    with open(path, "rb") as fh:
        requests.post(
            f"{_API}/sendVoice",
            data={"chat_id": chat_id},
            files={"voice": fh},
        )


def handle_message(chat_id: int, text: str) -> None:
    """Forward ``text`` to the GLM and return the reply."""
    signal_bus.publish("telegram:in", {"chat_id": chat_id, "content": text})
    reply = send_glm_command(text)
    send_message(chat_id, reply)
    try:
        from core import expressive_output

        audio = expressive_output.speak(reply, "neutral")
    except Exception:  # pragma: no cover - optional dependency
        logger.exception("Failed synthesizing voice")
        return
    send_voice(chat_id, audio)


if _API:
    signal_bus.subscribe(
        "telegram:out",
        lambda payload: send_message(
            int(payload.get("chat_id", 0)), payload.get("content", "")
        ),
    )


class TelegramConnector(ConnectorHeartbeat):
    """Telegram connector emitting heartbeats."""

    def __init__(self, *, interval: float = 30.0, miss_threshold: int = 3) -> None:
        super().__init__("telegram", interval=interval, miss_threshold=miss_threshold)

    def run(self) -> None:
        self.start()
        poll()


def poll() -> None:
    """Continuously poll Telegram for updates."""
    if not _API:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
    offset: int | None = None
    while True:
        try:
            res = requests.get(
                f"{_API}/getUpdates",
                params={"timeout": 30, "offset": offset},
                timeout=60,
            )
            res.raise_for_status()
            updates = res.json().get("result", [])
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                if "text" in msg and "chat" in msg:
                    handle_message(int(msg["chat"]["id"]), str(msg["text"]))
        except Exception:
            logger.exception("Polling failed")
            time.sleep(5)
        time.sleep(1)


def main() -> None:
    """Entry point for the Telegram bot."""
    TelegramConnector().run()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
