"""Tests for MemoryBundle layer initialization events."""

from __future__ import annotations

import importlib

from citadel.event_producer import Event, EventProducer

from agents.event_bus import set_event_producer
from memory import LAYERS, LAYER_STATUSES
from memory.bundle import MemoryBundle
import conftest as conftest_module
from pathlib import Path

conftest_module.ALLOWED_TESTS.update(
    {str(Path(__file__).resolve()), str(Path(__file__))}
)


class DummyProducer(EventProducer):
    """Capture events emitted via the event bus."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    async def emit(self, event: Event) -> None:  # pragma: no cover - trivial
        self.events.append(event)


def test_initialize_emits_event_and_sets_ready_statuses(monkeypatch):
    producer = DummyProducer()
    set_event_producer(producer)
    bundle = MemoryBundle()

    statuses = bundle.initialize()

    assert len(producer.events) == 1
    event = producer.events[0]
    assert event.event_type == "layer_init"
    assert event.payload["layers"] == statuses
    assert set(statuses) == set(LAYERS)
    assert all(statuses[layer] == "ready" for layer in LAYERS)
    set_event_producer(None)


def test_initialize_marks_defaulted_layer(monkeypatch):
    producer = DummyProducer()
    set_event_producer(producer)

    real_import = importlib.import_module

    class OptionalModule:
        __name__ = "memory.optional.mental"

    def fake_import(name: str):
        if name == "memory.mental":
            return OptionalModule()
        return real_import(name)

    monkeypatch.setattr("memory.bundle.import_module", fake_import)
    monkeypatch.setitem(LAYER_STATUSES, "mental", "defaulted")

    bundle = MemoryBundle()
    statuses = bundle.initialize()

    assert statuses["mental"] == "defaulted"
    assert producer.events[0].payload["layers"]["mental"] == "defaulted"
    set_event_producer(None)


def test_initialize_handles_import_error(monkeypatch):
    producer = DummyProducer()
    set_event_producer(producer)

    real_import = importlib.import_module

    def fake_import(name: str):
        if name == "memory.spiritual":
            raise ImportError("boom")
        return real_import(name)

    monkeypatch.setattr("memory.bundle.import_module", fake_import)
    monkeypatch.setitem(LAYER_STATUSES, "spiritual", "error")

    bundle = MemoryBundle()
    statuses = bundle.initialize()

    assert statuses["spiritual"] == "error"
    assert producer.events[0].payload["layers"]["spiritual"] == "error"
    set_event_producer(None)
