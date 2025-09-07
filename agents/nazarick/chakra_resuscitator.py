"""NAZARICK agent repairing chakras after heartbeat failures."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Callable, Dict

from agents.event_bus import emit_event, subscribe
from citadel.event_producer import Event

try:  # pragma: no cover - optional dependency
    from agents.razar.lifecycle_bus import LifecycleBus, Issue
except Exception:  # pragma: no cover - optional dependency
    LifecycleBus = None  # type: ignore[assignment]
    Issue = None  # type: ignore[assignment]

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
    """Listen for aggregator ``chakra_down`` events and attempt recovery."""

    def __init__(
        self,
        actions: Dict[str, Callable[[], bool]],
        emitter: Callable[[str, str, Dict[str, object]], None] = emit_event,
        bus: LifecycleBus | None = None,
        agent_id: str | None = None,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        self.actions = actions
        self.emit = emitter
        self.bus = bus
        # Resolve the current agent identifier for targeted events.
        self.agent_id = agent_id or os.getenv("AGENT_ID", "")
        self.retries = retries
        self.backoff = backoff

    # ------------------------------------------------------------------
    def resuscitate(self, chakra: str) -> bool:
        """Run the repair routine for ``chakra`` with retries."""

        action = self.actions.get(chakra)
        success = False
        start = time.time()
        if action:
            delay = self.backoff
            for attempt in range(1, self.retries + 1):
                try:
                    success = action()
                except Exception:  # pragma: no cover - unexpected failure
                    LOGGER.exception("Repair action failed for %s", chakra)
                    success = False
                if success:
                    break
                if attempt < self.retries:
                    LOGGER.debug("Retrying repair for %s in %s seconds", chakra, delay)
                    time.sleep(delay)
                    delay *= 2
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
        return success

    # ------------------------------------------------------------------
    async def handle_event(self, event: Event) -> None:
        """Process a ``chakra_down`` event from the event bus."""

        target = str(event.payload.get("target_agent", ""))
        if target and target != self.agent_id:
            LOGGER.info(
                "Ignoring event for agent %s (current agent %s)", target, self.agent_id
            )
            return

        chakra = str(event.payload.get("chakra"))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.resuscitate, chakra)

    # ------------------------------------------------------------------
    def handle_issue(self, issue: Issue) -> None:
        """Process a ``component_down`` issue from the lifecycle bus."""

        if issue.issue != "component_down":
            return
        chakra = issue.component
        success = self.resuscitate(chakra)
        if self.bus is not None:
            status = "repaired" if success else "repair_failed"
            self.bus.publish_status(chakra, status)

    # ------------------------------------------------------------------
    async def run(self, **subscribe_kwargs) -> None:
        """Subscribe to events and handle ``chakra_down`` notifications."""

        async def _handler(event: Event) -> None:
            if (
                event.agent_id == "chakra_heartbeat"
                and event.event_type == "chakra_down"
            ):
                await self.handle_event(event)

        await subscribe(_handler, **subscribe_kwargs)

    # ------------------------------------------------------------------
    def run_bus(self, *, limit: int | None = None) -> None:
        """Listen for lifecycle bus issues and invoke repairs."""

        if self.bus is None:
            raise RuntimeError("LifecycleBus instance required")
        count = 0
        for issue in self.bus.listen_for_issues():
            self.handle_issue(issue)
            count += 1
            if limit is not None and count >= limit:
                break


__all__ = ["ChakraResuscitator"]
