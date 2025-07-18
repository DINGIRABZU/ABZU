from __future__ import annotations

"""Telegram bot forwarding chat messages to the `/glm-command` endpoint."""

from pathlib import Path
import os
import time
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_API = f"https://api.telegram.org/bot{_TOKEN}" if _TOKEN else None
_GLM_URL = os.getenv("WEB_CONSOLE_API_URL", "http://localhost:8000/glm-command")


def send_glm_command(text: str) -> str:
    """Return response from the GLM command endpoint."""
    res = requests.post(_GLM_URL, json={"command": text}, timeout=60)
    res.raise_for_status()
    return res.json().get("result", "")


def send_message(chat_id: int, text: str) -> None:
    """Send ``text`` to ``chat_id`` via Telegram."""
    if not _API:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
    requests.post(f"{_API}/sendMessage", json={"chat_id": chat_id, "text": text})


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
    reply = send_glm_command(text)
    send_message(chat_id, reply)
    try:
        from core import expressive_output

        audio = expressive_output.speak(reply, "neutral")
    except Exception:  # pragma: no cover - optional dependency
        logger.exception("Failed synthesizing voice")
        return
    send_voice(chat_id, audio)


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
    poll()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
