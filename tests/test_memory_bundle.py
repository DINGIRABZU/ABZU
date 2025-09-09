"""Tests for MemoryBundle layer initialization events."""

from __future__ import annotations

import importlib

from citadel.event_producer import Event, EventProducer

from agents.event_bus import set_event_producer
from memory import LAYERS, LAYER_STATUSES
from memory.bundle import MemoryBundle

qm = importlib.import_module("memory.query_memory")
import pytest
from tests import conftest as conftest_module
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


@pytest.fixture
def stub_layer_queries(monkeypatch):
    """Stub individual layer query functions and record call order."""

    calls: list[str] = []

    def stub(name: str, value):
        def _stub(prompt: str):
            calls.append(name)
            return value

        return _stub

    monkeypatch.setattr(qm, "query_cortex", stub("cortex", ["c"]))
    monkeypatch.setattr(qm, "query_vector_store", stub("vector", ["v"]))
    monkeypatch.setattr(qm, "spiral_recall", stub("spiral", "s"))
    return calls


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


def test_initialize_marks_skipped_layer(monkeypatch):
    producer = DummyProducer()
    set_event_producer(producer)

    real_import = importlib.import_module

    class OptionalModule:
        __name__ = "memory.optional.mental"

    def fake_import(name: str):
        if name == "memory.mental":
            raise ModuleNotFoundError(name)
        if name == "memory.optional.mental":
            return OptionalModule()
        return real_import(name)

    monkeypatch.setattr("memory.bundle.import_module", fake_import)
    monkeypatch.setitem(LAYER_STATUSES, "mental", "skipped")

    bundle = MemoryBundle()
    statuses = bundle.initialize()

    assert statuses["mental"] == "skipped"
    assert producer.events[0].payload["layers"]["mental"] == "skipped"
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


def test_query_aggregates_results(stub_layer_queries):
    producer = DummyProducer()
    set_event_producer(producer)
    bundle = MemoryBundle()

    result = bundle.query("text")

    assert result == {
        "cortex": ["c"],
        "vector": ["v"],
        "spiral": "s",
        "failed_layers": [],
    }
    assert stub_layer_queries == ["cortex", "vector", "spiral"]

    assert len(producer.events) in (0, 1)
    if producer.events:
        assert producer.events[0].event_type == "query"
    set_event_producer(None)


@pytest.mark.parametrize("provider", ["noop", "opentelemetry"])
def test_memory_bundle_traces(monkeypatch, stub_layer_queries, provider):
    """MemoryBundle initializes and queries under different tracers."""

    if provider == "opentelemetry":
        pytest.importorskip("opentelemetry")

    monkeypatch.setenv("TRACE_PROVIDER", provider)
    import memory.bundle as bundle_module

    importlib.reload(bundle_module)

    producer = DummyProducer()
    set_event_producer(producer)
    bundle = bundle_module.MemoryBundle()

    statuses = bundle.initialize()
    assert set(statuses) == set(LAYERS)

    result = bundle.query("text")
    assert result == {
        "cortex": ["c"],
        "vector": ["v"],
        "spiral": "s",
        "failed_layers": [],
    }

    set_event_producer(None)
