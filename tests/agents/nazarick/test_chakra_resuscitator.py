"""Integration tests for :mod:`agents.nazarick.chakra_resuscitator`."""

from __future__ import annotations

import asyncio
import queue
from pathlib import Path

import pytest

from citadel.event_producer import Event

from agents.event_bus import set_event_producer
from agents.nazarick.chakra_resuscitator import ChakraResuscitator
from agents.razar.lifecycle_bus import Issue
import razar.recovery_manager as recovery_manager
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


class DummyBus:
    """Minimal in-memory lifecycle bus for testing."""

    def __init__(self) -> None:
        self.statuses: list[tuple[str, str]] = []
        self._issues: "queue.Queue[Issue]" = queue.Queue()

    def report_issue(self, component: str, issue: str) -> None:
        self._issues.put(Issue(component, issue))

    def listen_for_issues(self):
        while not self._issues.empty():
            yield self._issues.get()

    def publish_status(self, component: str, status: str) -> None:
        self.statuses.append((component, status))

    def send_control(self, component: str, action: str) -> None:  # pragma: no cover
        pass


def test_missed_heartbeat_triggers_repair(tmp_path: Path) -> None:
    """A missing heartbeat emits component_down and triggers repair."""
    # Integration ensures recovery_manager receives confirmation pulses.

    # Capture emitted confirmation events
    events: list[tuple[str, str, dict[str, object]]] = []

    def emitter(agent: str, event: str, payload: dict[str, object]) -> None:
        events.append((agent, event, payload))

    bus = DummyBus()
    resuscitator = ChakraResuscitator({"root": lambda: True}, emitter=emitter, bus=bus)

    # Avoid polluting the repository with state files
    recovery_manager.STATE_DIR = tmp_path
    recovery_manager.report_missed_heartbeat("root", bus=bus)

    resuscitator.run_bus(limit=1)

    assert ("root", "repaired") in bus.statuses
    assert events and events[0][1] == "chakra_resuscitated"
