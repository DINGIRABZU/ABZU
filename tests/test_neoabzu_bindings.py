import sys
import types
import pytest


def setup_event_bus():
    agents = types.ModuleType("agents")
    event_bus = types.ModuleType("event_bus")

    def emit_event(actor, action, metadata):
        pass

    event_bus.emit_event = emit_event
    sys.modules["agents"] = agents
    sys.modules["agents.event_bus"] = event_bus


def test_core_evaluate():
    core = pytest.importorskip("neoabzu_core")
    assert core.evaluate("(\\x.x)y") == "y"


def test_memory_bundle_initialize():
    memory = pytest.importorskip("neoabzu_memory")
    setup_event_bus()
    bundle = memory.MemoryBundle()
    statuses = bundle.initialize()
    assert "vector" in statuses


def test_vector_search():
    vector = pytest.importorskip("neoabzu_vector")
    res = vector.search("a", 1)
    assert res[0][0] == "a0"


def test_rag_retrieve_top():
    rag = pytest.importorskip("neoabzu_rag")
    setup_event_bus()
    vector_memory = types.ModuleType("vector_memory")

    def query_vectors(*a, **k):
        return [{"text": "abc"}]

    vector_memory.query_vectors = query_vectors
    sys.modules["vector_memory"] = vector_memory
    res = rag.retrieve_top("abc", 1)
    assert res[0]["text"] == "abc"
