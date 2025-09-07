"""NAZARICK agent restarting failed peers via lifecycle events."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict

from agents.event_bus import emit_event
from agents.razar import lifecycle_bus

LOGGER = logging.getLogger(__name__)


class Resuscitator:
    """Listen for ``agent_down`` events and attempt recovery."""

    def __init__(
        self,
        actions: Dict[str, Callable[[], bool]],
        emitter: Callable[[Dict[str, Any]], None] = lifecycle_bus.publish,
    ) -> None:
        self.actions = actions
        self.emit = emitter

    # ------------------------------------------------------------------
    def resuscitate(self, agent: str) -> bool:
        """Run the restart or patch routine for ``agent``."""

        action = self.actions.get(agent)
        success = bool(action and action())
        event = "agent_resuscitated" if success else "agent_resuscitation_failed"
        payload = {"event": event, "agent": agent}
        self.emit(payload)
        emit_event("nazarick", event, {"agent": agent})
        level = logging.INFO if success else logging.ERROR
        LOGGER.log(
            level,
            "%s agent %s",
            "Resuscitated" if success else "Failed to resuscitate",
            agent,
        )
        return success

    # ------------------------------------------------------------------
    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Process an ``agent_down`` event from the lifecycle bus."""

        if event.get("event") != "agent_down":
            return
        agent = str(event.get("agent"))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.resuscitate, agent)

    # ------------------------------------------------------------------
    async def run(self) -> None:
        """Subscribe to the lifecycle bus and remediate failures."""

        async for evt in lifecycle_bus.subscribe():
            await self.handle_event(evt)


__all__ = ["Resuscitator"]
