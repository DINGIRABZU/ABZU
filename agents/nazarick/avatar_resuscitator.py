"""NAZARICK agent restoring stalled avatar sessions."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Dict

from agents.event_bus import emit_event, subscribe
from citadel.event_producer import Event

LOGGER = logging.getLogger(__name__)
__version__ = "0.1.0"


class AvatarResuscitator:
    """Listen for ``avatar_down`` events and attempt recovery."""

    def __init__(
        self,
        actions: Dict[str, Callable[[], bool]],
        emitter: Callable[[str, str, Dict[str, object]], None] = emit_event,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        self.actions = actions
        self.emit = emitter
        self.retries = retries
        self.backoff = backoff

    def resuscitate(self, session: str) -> bool:
        """Run the repair routine for ``session`` with retries."""

        action = self.actions.get(session)
        success = False
        if action:
            delay = self.backoff
            for attempt in range(1, self.retries + 1):
                try:
                    success = action()
                except Exception:  # pragma: no cover - unexpected failure
                    LOGGER.exception("Repair action failed for %s", session)
                    success = False
                if success:
                    break
                if attempt < self.retries:
                    LOGGER.debug("Retrying repair for %s in %s seconds", session, delay)
                    time.sleep(delay)
                    delay *= 2
        if success:
            LOGGER.info("Resuscitated avatar session %s", session)
            self.emit("nazarick", "avatar_resuscitated", {"session": session})
        else:
            LOGGER.error("Failed to resuscitate avatar session %s", session)
            self.emit("nazarick", "avatar_resuscitation_failed", {"session": session})
        return success

    async def handle_event(self, event: Event) -> None:
        """Process an ``avatar_down`` event from the event bus."""

        if event.agent_id != "avatar_watchdog" or event.event_type != "avatar_down":
            return
        session = str(event.payload.get("session"))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.resuscitate, session)

    async def run(self, **subscribe_kwargs) -> None:
        """Subscribe to events and handle ``avatar_down`` notifications."""

        async def _handler(event: Event) -> None:
            await self.handle_event(event)

        await subscribe(_handler, **subscribe_kwargs)


__all__ = ["AvatarResuscitator"]
