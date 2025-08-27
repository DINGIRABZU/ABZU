from citadel.event_producer import Event, EventProducer

from agents.event_bus import emit_event, set_event_producer


class DummyProducer(EventProducer):
    def __init__(self) -> None:
        self.events = []

    async def emit(self, event: Event) -> None:  # pragma: no cover - simple
        self.events.append(event)


def test_emit_event_uses_configured_producer():
    producer = DummyProducer()
    set_event_producer(producer)

    emit_event("tester", "ran", {"x": 1})

    assert producer.events[0].agent_id == "tester"
    assert producer.events[0].event_type == "ran"
    assert producer.events[0].payload == {"x": 1}

    set_event_producer(None)
