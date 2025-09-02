"""Tests for citadel event processor."""

import asyncio
from unittest.mock import AsyncMock

from citadel.event_producer import Event
from citadel.event_processor import process_event


def test_process_event_writes_to_all_backends():
    event = Event(agent_id="a1", event_type="test", payload={})
    ts_writer = AsyncMock()
    neo_writer = AsyncMock()

    asyncio.run(process_event(event, ts_writer, neo_writer))

    ts_writer.write_event.assert_awaited_once_with(event)
    neo_writer.write_event.assert_awaited_once_with(event)
