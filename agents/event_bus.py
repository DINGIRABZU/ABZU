"""Simple event bus helper for agents.

This module exposes :func:`emit_event` which routes agent events through the
existing ``citadel`` event producers. A producer is created lazily based on
environment variables so tests and environments without a broker remain
functional. Consumers like ``nazarick.narrative_scribe`` can subscribe to the
same broker to receive these events.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

from .interaction_log import log_agent_interaction

from citadel.event_producer import (
    Event,
    EventProducer,
    RedisEventProducer,
    KafkaEventProducer,
)

_producer: Optional[EventProducer] = None


def set_event_producer(producer: EventProducer | None) -> None:
    """Explicitly configure the global :class:`EventProducer`.

    Passing ``None`` resets the producer and disables event emission. This is
    primarily intended for tests where a mock producer is supplied.
    """

    global _producer
    _producer = producer


def _get_producer() -> Optional[EventProducer]:
    """Return the configured :class:`EventProducer`, creating one if needed."""

    global _producer
    if _producer is not None:
        return _producer

    channel = os.getenv("CITADEL_REDIS_CHANNEL")
    topic = os.getenv("CITADEL_KAFKA_TOPIC")
    if channel:
        url = os.getenv("CITADEL_REDIS_URL", "redis://localhost")
        _producer = RedisEventProducer(channel=channel, url=url)
    elif topic:
        servers = os.getenv("CITADEL_KAFKA_SERVERS", "localhost:9092")
        _producer = KafkaEventProducer(topic=topic, bootstrap_servers=servers)
    return _producer


def emit_event(actor: str, action: str, metadata: Dict[str, Any]) -> None:
    """Emit an event for ``actor`` performing ``action`` with ``metadata``.

    The interaction is recorded to ``logs/agent_interactions.jsonl``. If no
    event producer is configured, the function still logs locally and quietly
    returns.
    """

    entry: Dict[str, Any] = {
        "source": actor,
        "action": action,
        "metadata": metadata,
        "function": "emit_event",
    }
    target = (
        metadata.get("target") or metadata.get("agent") or metadata.get("target_agent")
    )
    if isinstance(target, str):
        entry["target"] = target
    log_agent_interaction(entry)

    producer = _get_producer()
    if producer is None:
        return

    event = Event(agent_id=actor, event_type=action, payload=metadata)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(producer.emit(event))
    else:  # pragma: no cover - depends on event loop presence
        loop.create_task(producer.emit(event))


__all__ = ["emit_event", "set_event_producer"]
