"""Examples for memory bus and query aggregator."""

from citadel.event_producer import Event, EventProducer

from agents.event_bus import set_event_producer
import memory
from memory import publish_layer_event, query_memory


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
