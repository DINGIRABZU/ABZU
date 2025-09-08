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
from typing import Any, Awaitable, Callable, Dict, Optional

from opentelemetry import trace

from .interaction_log import log_agent_interaction

from citadel.event_producer import (
    Event,
    EventProducer,
    RedisEventProducer,
    KafkaEventProducer,
)
from worlds.config_registry import register_broker

_producer: Optional[EventProducer] = None
_tracer = trace.get_tracer(__name__)


def set_event_producer(producer: EventProducer | None) -> None:
    """Explicitly configure the global :class:`EventProducer`.

    Passing ``None`` resets the producer and disables event emission. This is
    primarily intended for tests where a mock producer is supplied.
    """

    with _tracer.start_as_current_span("event_bus.set_producer") as span:
        span.set_attribute(
            "event_bus.producer", getattr(producer, "__class__", type(None)).__name__
        )
        global _producer
        _producer = producer


def _get_producer() -> Optional[EventProducer]:
    """Return the configured :class:`EventProducer`, creating one if needed."""

    global _producer
    if _producer is not None:
        return _producer

    with _tracer.start_as_current_span("event_bus.producer") as span:
        channel = os.getenv("CITADEL_REDIS_CHANNEL")
        topic = os.getenv("CITADEL_KAFKA_TOPIC")
        if channel:
            url = os.getenv("CITADEL_REDIS_URL", "redis://localhost")
            span.set_attribute("event_bus.broker", "redis")
            span.set_attribute("event_bus.channel", channel)
            _producer = RedisEventProducer(channel=channel, url=url)
            register_broker("redis", {"channel": channel, "url": url})
        elif topic:
            servers = os.getenv("CITADEL_KAFKA_SERVERS", "localhost:9092")
            span.set_attribute("event_bus.broker", "kafka")
            span.set_attribute("event_bus.topic", topic)
            _producer = KafkaEventProducer(topic=topic, bootstrap_servers=servers)
            register_broker("kafka", {"topic": topic, "servers": servers})
        return _producer


def emit_event(actor: str, action: str, metadata: Dict[str, Any]) -> None:
    """Emit an event for ``actor`` performing ``action`` with ``metadata``.

    The interaction is recorded to ``logs/agent_interactions.jsonl``. If no
    event producer is configured, the function still logs locally and quietly
    returns.
    """

    with _tracer.start_as_current_span("agent.event") as span:
        span.set_attribute("agent.actor", actor)
        span.set_attribute("agent.action", action)
        for key, value in metadata.items():
            span.set_attribute(f"agent.metadata.{key}", str(value))

        entry: Dict[str, Any] = {
            "source": actor,
            "action": action,
            "metadata": metadata,
            "function": "emit_event",
        }
        target = (
            metadata.get("target")
            or metadata.get("agent")
            or metadata.get("target_agent")
        )
        if isinstance(target, str):
            entry["target"] = target
        log_agent_interaction(entry)

        producer = _get_producer()
        if producer is None:
            return

        event = Event(
            agent_id=actor,
            event_type=action,
            payload=metadata,
            target_agent=metadata.get("target_agent"),
        )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(producer.emit(event))
        else:  # pragma: no cover - depends on event loop presence
            loop.create_task(producer.emit(event))


async def subscribe(
    handler: Callable[[Event], Awaitable[None]],
    *,
    redis_channel: str | None = None,
    redis_url: str | None = None,
    kafka_topic: str | None = None,
    kafka_servers: str | None = None,
) -> None:
    """Subscribe to broker events and invoke ``handler`` for each message.

    The broker configuration is resolved from the arguments or matching
    ``CITADEL_*`` environment variables. The function runs until cancelled.
    """

    channel = redis_channel or os.getenv("CITADEL_REDIS_CHANNEL")
    topic = kafka_topic or os.getenv("CITADEL_KAFKA_TOPIC")

    with _tracer.start_as_current_span("event_bus.subscribe") as span:
        if channel:
            url = redis_url or os.getenv("CITADEL_REDIS_URL", "redis://localhost")
            span.set_attribute("event_bus.broker", "redis")
            span.set_attribute("event_bus.channel", channel)
            import redis.asyncio as redis  # type: ignore

            client = redis.from_url(url)
            pubsub = client.pubsub()
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                event = Event.from_json(message["data"])
                with _tracer.start_as_current_span("agent.event.consume") as evt_span:
                    evt_span.set_attribute("agent.actor", event.agent_id)
                    evt_span.set_attribute("agent.action", event.event_type)
                await handler(event)
        elif topic:
            servers = kafka_servers or os.getenv(
                "CITADEL_KAFKA_SERVERS", "localhost:9092"
            )
            span.set_attribute("event_bus.broker", "kafka")
            span.set_attribute("event_bus.topic", topic)
            from aiokafka import AIOKafkaConsumer  # type: ignore

            consumer = AIOKafkaConsumer(topic, bootstrap_servers=servers)
            await consumer.start()
            try:
                async for msg in consumer:
                    event = Event.from_json(msg.value.decode("utf-8"))
                    with _tracer.start_as_current_span(
                        "agent.event.consume"
                    ) as evt_span:
                        evt_span.set_attribute("agent.actor", event.agent_id)
                        evt_span.set_attribute("agent.action", event.event_type)
                    await handler(event)
            finally:
                await consumer.stop()


__all__ = ["emit_event", "set_event_producer", "subscribe"]
