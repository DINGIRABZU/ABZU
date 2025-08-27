from __future__ import annotations

"""FastAPI service that processes agent events."""

import asyncio
import contextlib
import json
from typing import Optional

from fastapi import FastAPI

from .event_producer import Event


class TimescaleWriter:
    """Persist events to TimescaleDB."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._conn: Optional[object] = None

    async def _connect(self) -> None:
        import asyncpg  # type: ignore

        self._conn = await asyncpg.connect(self.dsn)

    async def write_event(self, event: Event) -> None:
        if self._conn is None:
            await self._connect()
        await self._conn.execute(
            """
            INSERT INTO agent_events (agent_id, event_type, payload, ts)
            VALUES ($1, $2, $3, $4)
            """,
            event.agent_id,
            event.event_type,
            json.dumps(event.payload),
            event.timestamp,
        )


class Neo4jWriter:
    """Persist relationships between agents in Neo4j."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[object] = None

    async def _connect(self) -> None:
        from neo4j import AsyncGraphDatabase  # type: ignore

        self._driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))

    async def write_event(self, event: Event) -> None:
        if self._driver is None:
            await self._connect()
        async with self._driver.session() as session:  # type: ignore
            await session.execute_write(
                lambda tx: tx.run(
                    """
                    MERGE (a:Agent {id: $agent_id})
                    CREATE (a)-[:EMITTED {type: $event_type, ts: $ts}]->(:Event {payload: $payload})
                    """,
                    agent_id=event.agent_id,
                    event_type=event.event_type,
                    ts=event.timestamp,
                    payload=json.dumps(event.payload),
                )
            )


async def process_event(event: Event, ts_writer: TimescaleWriter, neo_writer: Neo4jWriter) -> None:
    """Write the event to all backends."""

    await ts_writer.write_event(event)
    await neo_writer.write_event(event)


async def _redis_listener(channel: str, url: str, ts_writer: TimescaleWriter, neo_writer: Neo4jWriter) -> None:
    import redis.asyncio as redis  # type: ignore

    redis_client = redis.from_url(url)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        event = Event.from_json(message["data"])
        await process_event(event, ts_writer, neo_writer)


async def _kafka_listener(topic: str, bootstrap_servers: str, ts_writer: TimescaleWriter, neo_writer: Neo4jWriter) -> None:
    from aiokafka import AIOKafkaConsumer  # type: ignore

    consumer = AIOKafkaConsumer(topic, bootstrap_servers=bootstrap_servers)
    await consumer.start()
    try:
        async for msg in consumer:
            event = Event.from_json(msg.value.decode("utf-8"))
            await process_event(event, ts_writer, neo_writer)
    finally:
        await consumer.stop()


def create_app(
    *,
    redis_channel: Optional[str] = None,
    redis_url: str = "redis://localhost",
    kafka_topic: Optional[str] = None,
    kafka_servers: str = "localhost:9092",
    timescale_dsn: str = "postgresql://localhost/spiral",
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "neo4j",
) -> FastAPI:
    """Create the event processing application."""

    app = FastAPI()
    ts_writer = TimescaleWriter(timescale_dsn)
    neo_writer = Neo4jWriter(neo4j_uri, neo4j_user, neo4j_password)

    @app.on_event("startup")
    async def _startup() -> None:
        app.state.tasks = []
        if redis_channel:
            task = asyncio.create_task(
                _redis_listener(redis_channel, redis_url, ts_writer, neo_writer)
            )
            app.state.tasks.append(task)
        if kafka_topic:
            task = asyncio.create_task(
                _kafka_listener(kafka_topic, kafka_servers, ts_writer, neo_writer)
            )
            app.state.tasks.append(task)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        for task in getattr(app.state, "tasks", []):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
