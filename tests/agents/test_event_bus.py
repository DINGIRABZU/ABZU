"""Tests for event bus."""

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


def test_emit_event_logs_to_file(tmp_path):
    producer = DummyProducer()
    set_event_producer(producer)

    log_file = tmp_path / "agent_interactions.jsonl"
    import agents.interaction_log as interaction_log

    interaction_log._LOG_PATH = log_file
    emit_event("tester", "ran", {"x": 1})
    content = log_file.read_text(encoding="utf-8").strip()
    assert "tester" in content
    set_event_producer(None)
