"""Telegram bot forwarding messages to the avatar.

- **Endpoint:** ``POST /telegram/webhook``
- **Auth:** Bot token
- **Linked services:** Nazarick Agents
"""

from __future__ import annotations

__version__ = "0.1.0"

import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

import connectors.signal_bus as signal_bus
from connectors.message_formatter import format_message
from .gateway import Gateway, authentication

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot that routes messages through ``Gateway``."""

    def __init__(self, token: str, gateway: Gateway) -> None:
        """Initialise bot with Telegram token and gateway."""
        self._gateway = gateway
        self._token = token
        self._application = Application.builder().token(token).build()
        self._application.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self._handle_message)
        )

        def _outbound(payload: dict) -> None:
            chat_id = payload.get("chat_id")
            text = payload.get("content", "")
            if chat_id is None:
                return

            async def _send() -> None:
                payload_text = format_message("telegram", text)
                await self._application.bot.send_message(
                    chat_id=int(chat_id), text=payload_text
                )

            self._application.create_task(_send())

        signal_bus.subscribe("telegram:out", _outbound)

    async def _handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.effective_user is None or update.message is None:
            return
        authentication.verify_token("telegram", self._token)
        user_id = str(update.effective_user.id)
        content = update.message.text or ""
        signal_bus.publish("telegram:in", {"user": user_id, "content": content})
        await self._gateway.handle_incoming("telegram", user_id, content)

    def run(self) -> None:
        """Start polling for messages."""
        logger.info("Starting Telegram bot")
        self._application.run_polling()


__all__ = ["TelegramBot"]
