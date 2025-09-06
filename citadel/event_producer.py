"""Interfaces for emitting agent events to message brokers."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Event:
    """Representation of an agent event."""

    agent_id: str
    event_type: str
    payload: Dict[str, Any]
    target_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_json(self) -> str:
        """Serialise the event to a JSON string."""

        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str) -> Event:
        """Deserialise an event from a JSON string."""

        raw = json.loads(data)
        raw["timestamp"] = datetime.fromisoformat(raw["timestamp"])
        return cls(**raw)


def _write_dead_letter(event: Event, error: Exception) -> None:
    """Persist events that could not be dispatched."""

    path = os.getenv("CITADEL_DEAD_LETTER_FILE", "dead_letter_events.jsonl")
    entry = {"event": asdict(event), "error": str(error)}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=str) + "\n")


class EventProducer:
    """Interface for event producers."""

    async def emit(self, event: Event) -> None:
        """Emit an event to the underlying broker."""

        raise NotImplementedError


class RedisEventProducer(EventProducer):
    """Publish events to a Redis channel."""

    def __init__(self, channel: str, url: str = "redis://localhost") -> None:
        self.channel = channel
        self.url = url
        self._redis: Any | None = None

    async def _connect(self) -> None:
        import redis.asyncio as redis  # type: ignore

        self._redis = redis.from_url(self.url)

    async def emit(self, event: Event) -> None:  # noqa: D401 - See base class
        if self._redis is None:
            await self._connect()
        assert self._redis is not None
        try:
            await self._redis.publish(self.channel, event.to_json())
        except Exception as err:  # pragma: no cover - network failure
            _write_dead_letter(event, err)


class KafkaEventProducer(EventProducer):
    """Publish events to a Kafka topic."""

    def __init__(self, topic: str, bootstrap_servers: str = "localhost:9092") -> None:
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self._producer: Any | None = None

    async def _connect(self) -> None:
        from aiokafka import AIOKafkaProducer  # type: ignore

        self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        await self._producer.start()  # type: ignore[union-attr]

    async def emit(self, event: Event) -> None:  # noqa: D401 - See base class
        if self._producer is None:
            await self._connect()
        assert self._producer is not None
        try:
            await self._producer.send_and_wait(
                self.topic, event.to_json().encode("utf-8")
            )
        except Exception as err:  # pragma: no cover - network failure
            _write_dead_letter(event, err)
