"""Integration tests for :mod:`agents.nazarick.chakra_resuscitator`."""

from __future__ import annotations

import asyncio
import pytest

from citadel.event_producer import Event

from agents.event_bus import set_event_producer
from agents.nazarick.chakra_resuscitator import ChakraResuscitator
from monitoring.chakra_heartbeat import ChakraHeartbeat


class DummyProducer:
    """Collects emitted events for inspection."""

    def __init__(self) -> None:  # pragma: no cover - trivial
        self.events = []

    async def emit(self, event: Event) -> None:  # pragma: no cover - trivial
        self.events.append(event)


def test_failed_pulse_triggers_remediation() -> None:
    """``chakra_down`` events from the heartbeat aggregator invoke repair."""

    producer = DummyProducer()
    set_event_producer(producer)

    heartbeat = ChakraHeartbeat(["heart"], window=0.0)
    heartbeat.beat("heart", timestamp=0.0)
    with pytest.raises(RuntimeError):
        heartbeat.check_alerts(now=1.0)

    # The aggregator should have emitted a chakra_down event.
    assert producer.events
    event = producer.events[0]

    called = False

    def repair() -> bool:
        nonlocal called
        called = True
        return True

    resuscitator = ChakraResuscitator({"heart": repair})
    asyncio.run(resuscitator.handle_event(event))

    assert called

    set_event_producer(None)
