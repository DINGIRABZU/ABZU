"""Examples for memory bus and query aggregator."""

from citadel.event_producer import Event, EventProducer

import logging
import pytest

from agents.event_bus import set_event_producer
import memory
import memory.query_memory as qm
from memory import broadcast_layer_event, query_memory
from memory.search_api import aggregate_search

from scripts import init_memory_layers
from memory import cortex, emotional, narrative_engine, spiritual
from memory.cortex import record_spiral, query_spirals
from memory.emotional import (
    log_emotion,
    fetch_emotion_history,
    get_connection as emotion_conn,
)
from memory.spiritual import (
    map_to_symbol,
    lookup_symbol_history,
    get_connection as spirit_conn,
)
from memory.narrative_engine import log_story, stream_stories

try:  # mental layer optional
    from memory.mental import record_task_flow, query_related_tasks
except Exception:  # pragma: no cover - dependency may be missing
    record_task_flow = query_related_tasks = None


class DummyProducer(EventProducer):
    def __init__(self) -> None:
        self.events = []

    async def emit(self, event: Event) -> None:  # pragma: no cover - simple
        self.events.append(event)


def test_broadcast_layer_event_emits():
    producer = DummyProducer()
    set_event_producer(producer)

    broadcast_layer_event(
        {
            "cortex": "seeded",
            "emotional": "seeded",
            "mental": "skipped",
            "spiritual": "seeded",
            "narrative": "seeded",
        }
    )

    assert len(producer.events) == 1
    layers = producer.events[0].payload["layers"]
    assert layers["cortex"] == "seeded"
    assert layers["mental"] == "skipped"
    set_event_producer(None)


def test_query_memory_aggregates(monkeypatch):
    monkeypatch.setattr(qm, "query_spirals", lambda **kw: ["c"])
    monkeypatch.setattr(qm, "query_vectors", lambda **kw: ["v"])
    monkeypatch.setattr(qm, "spiral_recall", lambda q: "s")

    res = query_memory("demo")
    assert res == {"cortex": ["c"], "vector": ["v"], "spiral": "s"}


@pytest.mark.parametrize(
    "broken,expected",
    [
        ("query_spirals", {"cortex": [], "vector": ["v"], "spiral": "s"}),
        ("query_vectors", {"cortex": ["c"], "vector": [], "spiral": "s"}),
        ("spiral_recall", {"cortex": ["c"], "vector": ["v"], "spiral": ""}),
    ],
)
def test_query_memory_partial_results(monkeypatch, caplog, broken, expected):
    monkeypatch.setattr(qm, "query_spirals", lambda **kw: ["c"])
    monkeypatch.setattr(qm, "query_vectors", lambda **kw: ["v"])
    monkeypatch.setattr(qm, "spiral_recall", lambda q: "s")

    def boom(*a, **k):
        raise RuntimeError("fail")

    monkeypatch.setattr(qm, broken, boom)
    msg = {
        "query_spirals": "cortex query failed",
        "query_vectors": "vector query failed",
        "spiral_recall": "spiral recall failed",
    }[broken]

    with caplog.at_level(logging.ERROR):
        res = query_memory("demo")

    assert res == expected
    assert any(msg in r.message for r in caplog.records)


def test_aggregate_search_ranks(monkeypatch):
    from types import SimpleNamespace
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    old = now - timedelta(days=1)

    monkeypatch.setattr(
        memory.search_api,
        "query_spirals",
        lambda text: [{"decision": {"result": "c"}, "timestamp": old.isoformat()}],
    )

    emo_entry = SimpleNamespace(vector=[0.1], timestamp=now)
    monkeypatch.setattr(
        memory.search_api,
        "fetch_emotion_history",
        lambda limit: [emo_entry],
    )

    monkeypatch.setattr(memory.search_api, "lookup_symbol_history", lambda q: [])
    monkeypatch.setattr(memory.search_api, "stream_stories", lambda: iter([]))
    monkeypatch.setattr(memory.search_api, "query_related_tasks", lambda q: [])

    res = aggregate_search("0.1", source_weights={"emotional": 2.0})
    assert res[0]["source"] == "emotional"


@pytest.mark.parametrize(
    "broken,missing",
    [
        ("query_spirals", "cortex"),
        ("fetch_emotion_history", "emotional"),
        ("query_related_tasks", "mental"),
        ("lookup_symbol_history", "spiritual"),
        ("stream_stories", "narrative"),
    ],
)
def test_aggregate_search_handles_missing_layers(monkeypatch, caplog, broken, missing):
    from types import SimpleNamespace
    from datetime import datetime

    now = datetime.utcnow()

    monkeypatch.setattr(
        memory.search_api,
        "query_spirals",
        lambda text: [{"decision": {"result": "c"}, "timestamp": now.isoformat()}],
    )
    emo_entry = SimpleNamespace(vector=[0.1], timestamp=now)
    monkeypatch.setattr(
        memory.search_api, "fetch_emotion_history", lambda limit: [emo_entry]
    )
    monkeypatch.setattr(memory.search_api, "query_related_tasks", lambda q: ["task"])
    monkeypatch.setattr(memory.search_api, "lookup_symbol_history", lambda q: ["sym"])
    monkeypatch.setattr(memory.search_api, "stream_stories", lambda: iter(["story"]))

    def boom(*a, **k):
        raise RuntimeError("fail")

    monkeypatch.setattr(memory.search_api, broken, boom)

    msg = {
        "query_spirals": "cortex search failed",
        "fetch_emotion_history": "emotional search failed",
        "query_related_tasks": "mental search failed",
        "lookup_symbol_history": "spiritual search failed",
        "stream_stories": "narrative search failed",
    }[broken]

    with caplog.at_level(logging.ERROR):
        res = aggregate_search("0.1")

    sources = {r["source"] for r in res}
    expected = {"cortex", "emotional", "mental", "spiritual", "narrative"} - {missing}
    assert sources == expected
    assert any(msg in r.message for r in caplog.records)


def test_init_memory_layers_bootstrap_and_persist(tmp_path, monkeypatch):
    """Boot layers via script and verify cross-layer event propagation."""

    # Route file-backed stores to a temporary directory
    monkeypatch.setattr(cortex, "CORTEX_MEMORY_FILE", tmp_path / "cortex.jsonl")
    monkeypatch.setattr(cortex, "CORTEX_INDEX_FILE", tmp_path / "cortex_index.json")
    monkeypatch.setattr(emotional, "DB_PATH", tmp_path / "emotions.db")
    monkeypatch.setenv("EMOTION_DB_PATH", str(tmp_path / "emotions.db"))
    monkeypatch.setattr(spiritual, "DB_PATH", tmp_path / "ontology.db")
    monkeypatch.setattr(narrative_engine, "DB_PATH", tmp_path / "narrative.db")
    monkeypatch.setattr(narrative_engine, "CHROMA_DIR", tmp_path / "narrative_chroma")

    # Ensure environment vars do not overwrite our paths
    monkeypatch.setenv("CORTEX_PATH", str(tmp_path / "cortex.jsonl"))
    monkeypatch.setenv("CORTEX_BACKEND", "file")
    monkeypatch.setenv("EMOTION_BACKEND", "file")
    monkeypatch.setenv("SPIRITUAL_DB_PATH", str(tmp_path / "ontology.db"))
    monkeypatch.setenv("NARRATIVE_LOG_PATH", str(tmp_path / "story.log"))

    producer = DummyProducer()
    set_event_producer(producer)

    init_memory_layers.main()

    assert len(producer.events) == 1
    layer_events = producer.events[0].payload["layers"]
    assert layer_events["cortex"] == "seeded"
    assert layer_events["emotional"] == "seeded"
    assert layer_events["spiritual"] == "seeded"
    assert layer_events["narrative"] == "seeded"
    assert "mental" in layer_events

    class Node:
        children = []

    record_spiral(Node(), {"result": "synthetic", "tags": ["cross"]})
    cortex_entries = query_spirals(tags=["cross"])
    assert any(e["decision"]["result"] == "synthetic" for e in cortex_entries)

    conn = emotion_conn(tmp_path / "emotions.db")
    logged = log_emotion([0.1], conn=conn)
    hist = fetch_emotion_history(60, conn=conn)
    assert any(abs(h.timestamp - logged.timestamp) < 1e-6 for h in hist)

    spirit = spirit_conn(tmp_path / "ontology.db")
    map_to_symbol(("omen", "\u263C"), conn=spirit)
    assert "omen" in lookup_symbol_history("\u263C", conn=spirit)

    log_story("synthetic tale")
    assert "synthetic tale" in list(stream_stories())

    if record_task_flow and query_related_tasks:
        record_task_flow("task1", {"key": "v"})
        record_task_flow("task2", {"key": "v"})
        assert "task2" in query_related_tasks("task1")
    else:
        assert layer_events["mental"] == "skipped"

    set_event_producer(None)
