"""Simple signal bus for cross-connector messaging.

The bus publishes and subscribes to chakra-tagged messages using either a
Redis backend (if configured) or an in-memory fallback. Each published
payload is automatically augmented with its chakra tag so listeners can
route messages by their origin.
"""

from __future__ import annotations

__version__ = "0.1.0"

from collections import defaultdict
import json
import os
import threading
from typing import Any, Callable, Dict, List

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore


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


def _get_bus() -> Any:
    url = os.getenv("SIGNAL_BUS_REDIS_URL")
    if url:
        try:
            return _RedisBus(url)
        except Exception:  # pragma: no cover - fallback to memory
            pass
    return _InMemoryBus()


_bus = _get_bus()


def publish(chakra: str, payload: Dict[str, Any]) -> None:
    """Publish ``payload`` tagged with ``chakra`` to all subscribers."""
    data = dict(payload)
    data.setdefault("chakra", chakra)
    _bus.publish(chakra, data)


def subscribe(
    chakra: str, callback: Callable[[Dict[str, Any]], None]
) -> Callable[[], None]:
    """Subscribe ``callback`` to messages for ``chakra``.

    Returns a callable that unsubscribes the callback when invoked.
    """
    return _bus.subscribe(chakra, callback)


__all__ = ["publish", "subscribe"]
