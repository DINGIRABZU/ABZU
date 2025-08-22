from __future__ import annotations

import asyncio

from communication.gateway import ChannelMessage, Gateway


class DummyCore:
    def __init__(self) -> None:
        self.received: ChannelMessage | None = None

    async def handle_message(self, message: ChannelMessage) -> None:  # pragma: no cover
        self.received = message


def test_gateway_routes_message() -> None:
    core = DummyCore()
    gateway = Gateway(core)
    asyncio.run(gateway.handle_incoming("telegram", "user123", "hello"))
    assert core.received == ChannelMessage(
        channel="telegram", user_id="user123", content="hello"
    )
