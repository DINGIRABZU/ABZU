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
from connectors.base import ConnectorHeartbeat
from connectors.message_formatter import format_message
from .gateway import Gateway, authentication

logger = logging.getLogger(__name__)


class TelegramBot(ConnectorHeartbeat):
    """Telegram bot that routes messages through ``Gateway`` with heartbeats."""

    def __init__(
        self,
        token: str,
        gateway: Gateway,
        *,
        interval: float = 30.0,
        miss_threshold: int = 3,
    ) -> None:
        """Initialise bot with Telegram token and gateway."""
        super().__init__("telegram", interval=interval, miss_threshold=miss_threshold)
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

        def _alert(payload: dict) -> None:
            logger.warning("Heartbeat alert: %s", payload)

        signal_bus.subscribe("telegram:alert", _alert)

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
        self.start()
        logger.info("Starting Telegram bot")
        self._application.run_polling()


__all__ = ["TelegramBot"]
