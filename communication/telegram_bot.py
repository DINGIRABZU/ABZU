from __future__ import annotations

"""Telegram bot forwarding messages to the avatar."""

import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .gateway import Gateway

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot that routes messages through ``Gateway``."""

    def __init__(self, token: str, gateway: Gateway) -> None:
        self._gateway = gateway
        self._application = Application.builder().token(token).build()
        self._application.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self._handle_message)
        )

    async def _handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.effective_user is None or update.message is None:
            return
        user_id = str(update.effective_user.id)
        content = update.message.text or ""
        await self._gateway.handle_incoming("telegram", user_id, content)

    def run(self) -> None:
        """Start polling for messages."""
        logger.info("Starting Telegram bot")
        self._application.run_polling()


__all__ = ["TelegramBot"]
