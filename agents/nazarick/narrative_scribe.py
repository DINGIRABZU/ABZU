# pydocstyle: skip-file
"""Narrative Scribe agent.

Listens to the Citadel event bus and converts agent events into prose.
Generated narratives are written to ``logs/nazarick_story.log`` and also
recorded via :func:`memory.narrative_engine.log_story`.
"""

from __future__ import annotations

__version__ = "0.1.1"

import asyncio
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

import yaml

from citadel.event_producer import Event
from memory import narrative_engine

LOG_FILE = Path("logs/nazarick_story.log")


@lru_cache(maxsize=1)
def _load_personas() -> Dict[str, Dict[str, str]]:
    """Load persona profiles from the adjacent YAML file."""

    path = Path(__file__).with_name("persona_profiles.yaml")
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("profiles", {})


class NarrativeScribe:
    """Convert events into narrative prose."""

    def __init__(self, personas: Dict[str, Dict[str, str]] | None = None) -> None:
        self.personas = personas or _load_personas()

    def _select_profile(self, agent_id: str) -> Dict[str, str]:
        return self.personas.get(agent_id, self.personas.get("default", {}))

    def compose(self, event: Event) -> str:
        """Return narrative text for ``event`` based on persona settings."""

        profile = self._select_profile(event.agent_id)
        template = profile.get("template", "{agent} {event_type} {payload}")
        tone = profile.get("tone", "")
        payload = json.dumps(event.payload, ensure_ascii=False)
        return template.format(
            agent=event.agent_id,
            event_type=event.event_type,
            payload=payload,
            tone=tone,
        )

    def process_event(self, event: Event) -> None:
        """Compose narrative for ``event`` and log it."""

        narrative = self.compose(event)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(narrative + "\n")
        narrative_engine.log_story(narrative)

    async def _redis_listener(self, channel: str, url: str) -> None:
        import redis.asyncio as redis  # type: ignore

        client = redis.from_url(url)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            event = Event.from_json(message["data"])
            self.process_event(event)

    async def _kafka_listener(self, topic: str, servers: str) -> None:
        from aiokafka import AIOKafkaConsumer  # type: ignore

        consumer = AIOKafkaConsumer(topic, bootstrap_servers=servers)
        await consumer.start()
        try:
            async for msg in consumer:
                event = Event.from_json(msg.value.decode("utf-8"))
                self.process_event(event)
        finally:
            await consumer.stop()

    async def run(
        self,
        *,
        redis_channel: str | None = None,
        redis_url: str = "redis://localhost",
        kafka_topic: str | None = None,
        kafka_servers: str = "localhost:9092",
    ) -> None:
        """Start listening to configured event sources."""

        tasks = []
        if redis_channel:
            tasks.append(
                asyncio.create_task(self._redis_listener(redis_channel, redis_url))
            )
        if kafka_topic:
            tasks.append(
                asyncio.create_task(self._kafka_listener(kafka_topic, kafka_servers))
            )
        if not tasks:
            raise ValueError("No event sources configured")
        await asyncio.gather(*tasks)


__all__ = ["NarrativeScribe", "LOG_FILE"]
