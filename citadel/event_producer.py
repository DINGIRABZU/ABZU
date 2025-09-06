"""Interfaces for emitting agent events to message brokers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Event:
    """Representation of an agent event."""

    agent_id: str
    event_type: str
    payload: Dict[str, Any]
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
        self._redis: Optional[object] = None

    async def _connect(self) -> None:
        import redis.asyncio as redis  # type: ignore

        self._redis = redis.from_url(self.url)

    async def emit(self, event: Event) -> None:  # noqa: D401 - See base class
        if self._redis is None:
            await self._connect()
        await self._redis.publish(self.channel, event.to_json())  # type: ignore[union-attr]


class KafkaEventProducer(EventProducer):
    """Publish events to a Kafka topic."""

    def __init__(self, topic: str, bootstrap_servers: str = "localhost:9092") -> None:
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self._producer: Optional[object] = None

    async def _connect(self) -> None:
        from aiokafka import AIOKafkaProducer  # type: ignore

        self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        await self._producer.start()  # type: ignore[union-attr]

    async def emit(self, event: Event) -> None:  # noqa: D401 - See base class
        if self._producer is None:
            await self._connect()
        await self._producer.send_and_wait(self.topic, event.to_json().encode("utf-8"))  # type: ignore[union-attr]
