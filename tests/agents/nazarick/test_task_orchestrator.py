"""Tests for :mod:`agents.task_orchestrator`."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from citadel.event_producer import Event, EventProducer

from agents.event_bus import set_event_producer
from agents.task_orchestrator import TaskOrchestrator


class DummyProducer(EventProducer):
    def __init__(self) -> None:  # pragma: no cover - trivial
        self.events: list[Event] = []

    async def emit(self, event: Event) -> None:  # pragma: no cover - trivial
        self.events.append(event)


def _write_registry(tmp_path: Path) -> Path:
    registry = {
        "agents": [
            {
                "id": "a1",
                "launch": "",
                "capabilities": ["compute"],
                "triggers": ["process"],
            },
            {
                "id": "a2",
                "launch": "",
                "capabilities": ["compute"],
                "triggers": ["process"],
            },
            {
                "id": "b1",
                "launch": "",
                "capabilities": ["store"],
                "triggers": ["save"],
            },
        ]
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry))
    return path


def test_dispatches_to_all_agents_with_capability(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)
    orchestrator = TaskOrchestrator(registry_path)
    producer = DummyProducer()
    set_event_producer(producer)

    event = Event(
        agent_id="tester", event_type="process", payload={"capability": "compute"}
    )
    asyncio.run(orchestrator.handle_event(event))

    targets = {evt.payload["target_agent"] for evt in producer.events}
    assert targets == {"a1", "a2"}

    set_event_producer(None)


def test_no_dispatch_when_capability_unknown(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)
    orchestrator = TaskOrchestrator(registry_path)
    producer = DummyProducer()
    set_event_producer(producer)

    event = Event(
        agent_id="tester", event_type="process", payload={"capability": "unknown"}
    )
    asyncio.run(orchestrator.handle_event(event))

    assert producer.events == []

    set_event_producer(None)
