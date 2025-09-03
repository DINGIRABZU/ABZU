"""Examples for memory bus and query aggregator."""

from citadel.event_producer import Event, EventProducer

from agents.event_bus import set_event_producer
import memory
from memory import publish_layer_event, query_memory

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


def test_publish_layer_event_emits():
    producer = DummyProducer()
    set_event_producer(producer)

    publish_layer_event("cortex", "seeded")

    assert producer.events[0].payload == {"layer": "cortex", "status": "seeded"}
    set_event_producer(None)


def test_query_memory_aggregates(monkeypatch):
    monkeypatch.setattr(memory, "query_spirals", lambda **kw: ["c"])
    monkeypatch.setattr(memory, "query_vectors", lambda **kw: ["v"])
    monkeypatch.setattr(memory, "spiral_recall", lambda q: "s")

    res = query_memory("demo")
    assert res == {"cortex": ["c"], "vector": ["v"], "spiral": "s"}


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

    layer_events = {e.payload["layer"]: e.payload["status"] for e in producer.events}
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
