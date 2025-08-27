import asyncio

from citadel.event_producer import Event, EventProducer


class MockProducer(EventProducer):
    def __init__(self) -> None:
        self.events = []

    async def emit(self, event: Event) -> None:
        self.events.append(event)


def test_event_serialisation_round_trip() -> None:
    event = Event(agent_id="a1", event_type="test", payload={"x": 1})
    restored = Event.from_json(event.to_json())
    assert restored == event


def test_mock_producer_emits_event() -> None:
    producer = MockProducer()
    event = Event(agent_id="a1", event_type="ping", payload={})
    asyncio.run(producer.emit(event))
    assert producer.events == [event]
