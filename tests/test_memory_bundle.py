"""Tests for MemoryBundle layer initialization events."""

from __future__ import annotations

import builtins
import importlib
import sys
import types

from citadel.event_producer import Event, EventProducer

from agents.event_bus import set_event_producer
from memory import LAYERS, LAYER_STATUSES
from memory.bundle import MemoryBundle

qm = importlib.import_module("memory.query_memory")
import pytest
from pathlib import Path
from tests import conftest as conftest_module

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

    def install_module(name: str, func_name: str, record: str, return_value):
        module = types.ModuleType(name)

        def _stub(*args, **kwargs):
            calls.append(record)
            return return_value

        setattr(module, func_name, _stub)
        monkeypatch.setitem(sys.modules, name, module)
        if "." in name:
            parent_name, attr = name.rsplit(".", 1)
            parent_module = sys.modules.get(parent_name)
            if parent_module is not None:
                monkeypatch.setattr(parent_module, attr, module, raising=False)

    install_module("memory.cortex", "query_spirals", "cortex", ["c"])
    install_module("vector_memory", "query_vectors", "vector", ["v"])
    install_module("spiral_memory", "spiral_recall", "spiral", "s")
    install_module("memory.emotional", "fetch_emotion_history", "emotional", ["e"])
    install_module("memory.mental", "query_related_tasks", "mental", ["m"])
    install_module("memory.spiritual", "lookup_symbol_history", "spiritual", ["p"])
    install_module("memory.narrative_engine", "stream_stories", "narrative", ["n"])
    install_module("neoabzu_core", "evaluate", "core", "core")

    return calls


def test_initialize_emits_event_and_sets_ready_statuses(monkeypatch):
    producer = DummyProducer()
    set_event_producer(producer)
    bundle = MemoryBundle()
    stubbed = getattr(bundle, "stubbed", False)

    statuses = bundle.initialize()

    assert len(producer.events) == 1
    event = producer.events[0]
    assert event.event_type == "layer_init"
    assert event.payload["layers"] == statuses
    expected_layers = set(LAYERS) | {"core"}
    assert set(statuses) == expected_layers
    assert set(bundle.diagnostics) == expected_layers
    if stubbed:
        for layer in statuses:
            assert statuses[layer] == "skipped"
            diag = bundle.diagnostics[layer]
            assert diag["status"] == "skipped"
            assert diag["loaded_module"].endswith("neoabzu_bundle")
            assert diag["fallback_reason"]
    else:
        for layer in LAYERS:
            assert bundle.diagnostics[layer]["status"] == statuses[layer]
        assert bundle.diagnostics["core"]["status"] == statuses["core"]
    set_event_producer(None)


def test_initialize_marks_skipped_layer(monkeypatch):
    if getattr(MemoryBundle(), "stubbed", False):
        pytest.skip("Global stub active; layer import fallbacks not exercised")

    producer = DummyProducer()
    set_event_producer(producer)

    real_import = builtins.__import__

    def fake_import(name: str, globals=None, locals=None, fromlist=(), level=0):
        if name == "memory.mental":
            raise ModuleNotFoundError(name)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "memory.mental", raising=False)
    monkeypatch.delitem(sys.modules, "memory.optional.mental", raising=False)
    monkeypatch.setitem(LAYER_STATUSES, "mental", "skipped")

    bundle = MemoryBundle()
    statuses = bundle.initialize()
    diag = bundle.diagnostics["mental"]

    assert statuses["mental"] == "skipped"
    assert producer.events[0].payload["layers"]["mental"] == "skipped"
    assert diag["status"] == "skipped"
    assert diag["fallback_reason"] == "primary_module_not_found"
    assert diag["loaded_module"].endswith("memory.optional.mental")
    attempts = diag["attempts"]
    assert attempts[0]["module"] == "memory.mental"
    assert attempts[0]["outcome"] == "error"
    assert attempts[1]["module"].endswith("memory.optional.mental")
    assert attempts[1]["outcome"] == "loaded"
    set_event_producer(None)


def test_initialize_handles_import_error(monkeypatch):
    if getattr(MemoryBundle(), "stubbed", False):
        pytest.skip("Global stub active; layer import fallbacks not exercised")

    producer = DummyProducer()
    set_event_producer(producer)

    real_import = builtins.__import__

    def fake_import(name: str, globals=None, locals=None, fromlist=(), level=0):
        if name == "memory.spiritual":
            raise ImportError("boom")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "memory.spiritual", raising=False)
    monkeypatch.setitem(LAYER_STATUSES, "spiritual", "error")

    bundle = MemoryBundle()
    statuses = bundle.initialize()
    diag = bundle.diagnostics["spiritual"]

    assert statuses["spiritual"] == "error"
    assert producer.events[0].payload["layers"]["spiritual"] == "error"
    assert diag["status"] == "error"
    assert diag["failure_reason"] == "primary_import_failed"
    attempts = diag["attempts"]
    assert attempts[0]["module"] == "memory.spiritual"
    assert attempts[0]["outcome"] == "error"
    assert "boom" in attempts[0]["error"]
    set_event_producer(None)


def test_query_aggregates_results(stub_layer_queries):
    producer = DummyProducer()
    set_event_producer(producer)
    bundle = MemoryBundle()
    stubbed = getattr(bundle, "stubbed", False)

    result = bundle.query("text")

    if stubbed:
        assert result["stubbed"] is True
        assert result["failed_layers"] == []
        for layer in (
            "cortex",
            "vector",
            "spiral",
            "emotional",
            "mental",
            "spiritual",
            "narrative",
        ):
            assert layer in result
    else:
        assert result == {
            "cortex": ["c"],
            "vector": ["v"],
            "spiral": "s",
            "emotional": ["e"],
            "mental": ["m"],
            "spiritual": ["p"],
            "narrative": ["n"],
            "core": "core",
            "failed_layers": [],
        }
        assert stub_layer_queries == [
            "cortex",
            "vector",
            "spiral",
            "emotional",
            "mental",
            "spiritual",
            "narrative",
            "core",
        ]

    assert len(producer.events) in (0, 1)
    if producer.events:
        if stubbed:
            assert producer.events[0].event_type == "layer_init"
        else:
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
    expected_layers = set(LAYERS) | {"core"}
    assert set(statuses) == expected_layers

    result = bundle.query("text")
    if getattr(bundle, "stubbed", False):
        assert result["stubbed"] is True
    else:
        assert result == {
            "cortex": ["c"],
            "vector": ["v"],
            "spiral": "s",
            "emotional": ["e"],
            "mental": ["m"],
            "spiritual": ["p"],
            "narrative": ["n"],
            "core": "core",
            "failed_layers": [],
        }

    set_event_producer(None)


def test_stubbed_bundle_diagnostics():
    bundle = MemoryBundle()
    if not getattr(bundle, "stubbed", False):
        pytest.skip("neoabzu_memory available; stub diagnostics not emitted")

    statuses = bundle.initialize()
    assert all(status == "skipped" for status in statuses.values())
    for layer, diag in bundle.diagnostics.items():
        assert diag["status"] == "skipped"
        assert diag["fallback_reason"] == "neoabzu_memory_unavailable"
        assert diag["loaded_module"].endswith("memory.optional.neoabzu_bundle")
        attempts = diag["attempts"]
        assert attempts[0]["module"] == "neoabzu_memory"
        assert attempts[0]["outcome"] == "error"
        assert attempts[1]["module"] == "memory.optional.neoabzu_bundle"
        assert attempts[1]["outcome"] == "loaded"
