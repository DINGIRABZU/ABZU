"""NAZARICK agent repairing chakras after heartbeat failures."""

from __future__ import annotations

import logging
import os
import time
from typing import Callable, Dict

from agents.event_bus import emit_event, subscribe
from citadel.event_producer import Event

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram
    from agents.razar.health_checks import init_metrics as _init_metrics

    _init_metrics()
except Exception:  # pragma: no cover - metrics are optional
    Counter = Histogram = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)

RESUSCITATION_COUNTER = (
    Counter(
        "chakra_resuscitation_attempts_total",
        "Number of resuscitation attempts",  # total attempts
        ["chakra", "outcome"],
    )
    if Counter
    else None
)
RESUSCITATION_DURATION = (
    Histogram(
        "chakra_resuscitation_duration_seconds",
        "Duration of resuscitation attempts in seconds",
        ["chakra"],
    )
    if Histogram
    else None
)


class ChakraResuscitator:
    """Listen for ``chakra_down`` events and attempt recovery."""

    def __init__(
        self,
        actions: Dict[str, Callable[[], bool]],
        emitter: Callable[[str, str, Dict[str, object]], None] = emit_event,
        agent_id: str | None = None,
    ) -> None:
        self.actions = actions
        self.emit = emitter
        # Resolve the current agent identifier for targeted events.
        self.agent_id = agent_id or os.getenv("AGENT_ID", "")

    async def handle_event(self, event: Event) -> None:
        """Process a ``chakra_down`` event."""

        target = str(event.payload.get("target_agent", ""))
        if target and target != self.agent_id:
            LOGGER.info(
                "Ignoring event for agent %s (current agent %s)", target, self.agent_id
            )
            return

        chakra = str(event.payload.get("chakra"))
        action = self.actions.get(chakra)
        success = False
        start = time.time()
        if action:
            try:
                success = action()
            except Exception:  # pragma: no cover - unexpected failure
                LOGGER.exception("Repair action failed for %s", chakra)
        duration = time.time() - start
        if RESUSCITATION_DURATION is not None:
            RESUSCITATION_DURATION.labels(chakra).observe(duration)
        outcome = "success" if success else "failure"
        if RESUSCITATION_COUNTER is not None:
            RESUSCITATION_COUNTER.labels(chakra, outcome).inc()
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
