"""Tests for vanna_data agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Iterator

import pytest

from agents import set_event_producer
from agents.vanna_data import query_db


class DummyDF:
    def __init__(self, records: List[Dict[str, Any]]) -> None:
        self._records = records

    def to_dict(self, orient: str) -> List[Dict[str, Any]]:  # pragma: no cover
        assert orient == "records"
        return self._records


class DummyProducer:
    def __init__(self) -> None:
        self.events: List[Any] = []

    async def emit(self, event: Any) -> None:  # pragma: no cover - simple
        self.events.append(event)


@dataclass
class Captured:
    contexts: List[Dict[str, Any]]
    narratives: List[Any]
    events: List[Any]


@pytest.fixture
def capture_env(mocker: Any) -> Iterator[Captured]:
    contexts: List[Dict[str, Any]] = []
    narratives: List[Any] = []

    mocker.patch(
        "agents.vanna_data.vanna.ask",
        return_value=("SELECT 1", DummyDF([{"x": 1}]), None),
    )
    mocker.patch(
        "agents.vanna_data.record_task_flow",
        side_effect=lambda _id, ctx: contexts.append(ctx),
    )
    mocker.patch(
        "agents.vanna_data._narrative_engine.record",
        side_effect=lambda ev: narratives.append(ev),
    )

    producer = DummyProducer()
    set_event_producer(producer)

    yield Captured(contexts, narratives, producer.events)

    set_event_producer(None)


def test_query_db_records_sql_and_events(capture_env: Captured) -> None:
    rows = query_db("test prompt")

    assert rows == [{"x": 1}]
    assert capture_env.contexts[0]["sql"] == "SELECT 1"
    assert capture_env.narratives[0].symbolism == "SELECT 1"
    assert capture_env.events[0].event_type == "task_delegated"
    assert capture_env.events[1].event_type == "task_completed"
    assert capture_env.narratives[0].actor == "vanna_data"
