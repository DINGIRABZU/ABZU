import asyncio

from agents.razar import lifecycle_bus


def test_publish_subscribe_roundtrip() -> None:
    async def runner() -> dict[str, object]:
        iterator = lifecycle_bus.subscribe()
        lifecycle_bus.publish({"event": "ping"})
        event = await asyncio.wait_for(iterator.__anext__(), timeout=1.0)
        await iterator.aclose()
        return event

    event = asyncio.run(runner())
    assert event == {"event": "ping"}
