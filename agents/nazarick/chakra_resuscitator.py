"""NAZARICK agent repairing chakras after heartbeat failures."""

from __future__ import annotations

import logging
from typing import Callable, Dict

from agents.event_bus import emit_event, subscribe
from citadel.event_producer import Event

LOGGER = logging.getLogger(__name__)


class ChakraResuscitator:
    """Listen for ``chakra_down`` events and attempt recovery."""

    def __init__(
        self,
        actions: Dict[str, Callable[[], bool]],
        emitter: Callable[[str, str, Dict[str, object]], None] = emit_event,
    ) -> None:
        self.actions = actions
        self.emit = emitter

    async def handle_event(self, event: Event) -> None:
        """Process a ``chakra_down`` event."""

        chakra = str(event.payload.get("chakra"))
        action = self.actions.get(chakra)
        success = False
        if action:
            try:
                success = action()
            except Exception:  # pragma: no cover - unexpected failure
                LOGGER.exception("Repair action failed for %s", chakra)
        if success:
            LOGGER.info("Resuscitated chakra %s", chakra)
            self.emit("nazarick", "chakra_resuscitated", {"chakra": chakra})
        else:
            LOGGER.error("Failed to resuscitate chakra %s", chakra)
            self.emit("nazarick", "chakra_resuscitation_failed", {"chakra": chakra})

    async def run(self, **subscribe_kwargs) -> None:
        """Subscribe to events and handle ``chakra_down`` notifications."""

        async def _handler(event: Event) -> None:
            if event.event_type == "chakra_down":
                await self.handle_event(event)

        await subscribe(_handler, **subscribe_kwargs)


__all__ = ["ChakraResuscitator"]
