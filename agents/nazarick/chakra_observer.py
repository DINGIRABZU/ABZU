from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable, Dict

from citadel.event_producer import Event

from agents.event_bus import emit_event, subscribe
from .chakra_resuscitator import ChakraResuscitator

LOGGER = logging.getLogger(__name__)

REGISTRY_FILE = Path(__file__).with_name("agent_registry.json")


class NazarickChakraObserver:
    """Observe chakra events targeted at this agent and trigger recovery."""

    def __init__(
        self,
        agent_id: str,
        action: Callable[[], bool],
        emitter: Callable[[str, str, Dict[str, object]], None] = emit_event,
    ) -> None:
        self.agent_id = agent_id
        self.chakra = self._lookup_chakra(agent_id)
        self.resuscitator = ChakraResuscitator({self.chakra: action}, emitter=emitter)

    @staticmethod
    def _lookup_chakra(agent_id: str) -> str:
        """Return the chakra associated with ``agent_id`` from the registry."""

        try:
            data = json.loads(REGISTRY_FILE.read_text())
        except FileNotFoundError:
            LOGGER.warning("Agent registry not found at %s", REGISTRY_FILE)
            return ""
        except Exception as exc:  # pragma: no cover - unexpected errors
            LOGGER.warning("Failed to load agent registry %s: %s", REGISTRY_FILE, exc)
            return ""
        for entry in data.get("agents", []):
            if entry.get("id") == agent_id:
                return str(entry.get("chakra", ""))
        LOGGER.warning("No chakra mapping found for agent %s", agent_id)
        return ""

    async def handle_event(self, event: Event) -> None:
        """Process events, delegating to the resuscitator when targeted."""

        if event.payload.get("target_agent") == self.agent_id:
            await self.resuscitator.handle_event(event)

    async def run(self, **subscribe_kwargs) -> None:
        """Subscribe to the event bus and monitor for targeted events."""

        async def _handler(event: Event) -> None:
            await self.handle_event(event)

        await subscribe(_handler, **subscribe_kwargs)


__all__ = ["NazarickChakraObserver"]
