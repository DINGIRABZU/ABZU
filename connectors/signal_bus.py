"""Simple signal bus for cross-connector messaging.

The bus publishes and subscribes to chakra-tagged messages using either a
Redis or Kafka backend (if configured) with an in-memory fallback. Each
published payload is automatically augmented with its chakra tag so listeners
can route messages by their origin.
"""

from __future__ import annotations

__version__ = "0.3.0"

from collections import defaultdict
import json
import os
import threading
from typing import Any, Callable, Dict, List

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from kafka import KafkaConsumer, KafkaProducer  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    KafkaConsumer = KafkaProducer = None  # type: ignore


class _InMemoryBus:
    """Fallback bus using in-process callbacks."""

    def __init__(self) -> None:
        self._subs: Dict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(
            list
        )
        self._lock = threading.Lock()

    def publish(self, chakra: str, payload: Dict[str, Any]) -> None:
        for cb in list(self._subs.get(chakra, [])):
            cb(payload)

    def subscribe(
        self, chakra: str, callback: Callable[[Dict[str, Any]], None]
    ) -> Callable[[], None]:
        with self._lock:
            self._subs[chakra].append(callback)

        def _unsubscribe() -> None:
            with self._lock:
                self._subs[chakra].remove(callback)

        return _unsubscribe


class _RedisBus:
    """Redis pub/sub based bus."""

    def __init__(self, url: str) -> None:
        if redis is None:  # pragma: no cover - optional dependency
            raise RuntimeError("redis library not installed")
        self._client = redis.from_url(url)  # type: ignore[attr-defined]

    def publish(self, chakra: str, payload: Dict[str, Any]) -> None:
        self._client.publish(chakra, json.dumps(payload))

    def subscribe(
        self, chakra: str, callback: Callable[[Dict[str, Any]], None]
    ) -> Callable[[], None]:
        pubsub = self._client.pubsub()
        pubsub.subscribe(chakra)

        def _listen() -> None:
            for msg in pubsub.listen():
                if msg.get("type") != "message":
                    continue
                data = json.loads(msg.get("data", b"{}"))
                callback(data)

        thread = threading.Thread(target=_listen, daemon=True)
        thread.start()

        def _unsubscribe() -> None:
            pubsub.unsubscribe(chakra)
            pubsub.close()

        return _unsubscribe


class _KafkaBus:
    """Kafka based bus."""

    def __init__(self, brokers: str) -> None:
        if (
            KafkaProducer is None or KafkaConsumer is None
        ):  # pragma: no cover - optional dependency
            raise RuntimeError("kafka library not installed")
        self._producer = KafkaProducer(bootstrap_servers=brokers)  # type: ignore[call-arg]
        self._brokers = brokers

    def publish(self, chakra: str, payload: Dict[str, Any]) -> None:
        self._producer.send(chakra, json.dumps(payload).encode("utf-8"))
        try:
            self._producer.flush()
        except Exception:  # pragma: no cover - network errors
            pass

    def subscribe(
        self, chakra: str, callback: Callable[[Dict[str, Any]], None]
    ) -> Callable[[], None]:
        consumer = KafkaConsumer(
            chakra, bootstrap_servers=self._brokers, auto_offset_reset="latest"
        )

        def _listen() -> None:
            for msg in consumer:
                try:
                    data = json.loads(msg.value.decode("utf-8"))
                except Exception:  # pragma: no cover - malformed payload
                    data = {}
                callback(data)

        thread = threading.Thread(target=_listen, daemon=True)
        thread.start()

        def _unsubscribe() -> None:
            consumer.close()

        return _unsubscribe


def _get_bus() -> Any:
    url = os.getenv("SIGNAL_BUS_REDIS_URL")
    if url:
        try:
            return _RedisBus(url)
        except Exception:  # pragma: no cover - fallback to other backends
            pass
    brokers = os.getenv("SIGNAL_BUS_KAFKA_BROKERS")
    if brokers:
        try:
            return _KafkaBus(brokers)
        except Exception:  # pragma: no cover - fallback to memory
            pass
    return _InMemoryBus()


_bus = _get_bus()


def publish(chakra: str, payload: Dict[str, Any], cycle_count: int) -> None:
    """Publish ``payload`` tagged with ``chakra`` and ``cycle_count``."""
    data = dict(payload)
    data.setdefault("chakra", chakra)
    data.setdefault("cycle", cycle_count)
    _bus.publish(chakra, data)


def subscribe(
    chakra: str, callback: Callable[[Dict[str, Any]], None]
) -> Callable[[], None]:
    """Subscribe ``callback`` to messages for ``chakra``.

    Returns a callable that unsubscribes the callback when invoked.
    """
    return _bus.subscribe(chakra, callback)


__all__ = ["publish", "subscribe"]
