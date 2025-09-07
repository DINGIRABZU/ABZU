"""Redis-backed helper for off-box vector memory backups."""

from __future__ import annotations

__version__ = "0.1.2"

import json
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

try:  # pragma: no cover - optional dependency
    import redis
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore


class DistributedMemory:
    """Store vector entries in Redis for distributed persistence."""

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        *,
        key: str = "vector_memory",
        client: Any | None = None,
    ) -> None:
        if redis is None:  # pragma: no cover - dependency check
            raise RuntimeError("redis package required for DistributedMemory")
        self.client = client or redis.Redis.from_url(url)
        self.key = key

    # ------------------------------------------------------------------
    def backup(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:
        payload = json.dumps({"vector": list(vector), "metadata": metadata})
        self.client.hset(self.key, id_, payload)

    # ------------------------------------------------------------------
    def restore(self) -> Dict[str, Tuple[list[float], Dict[str, Any]]]:
        out: Dict[str, Tuple[list[float], Dict[str, Any]]] = {}
        for key, val in self.client.hgetall(self.key).items():
            data = json.loads(val)
            out[key.decode()] = (data["vector"], data["metadata"])
        return out

    # ------------------------------------------------------------------
    def restore_to(self, store: Any) -> None:
        for id_, (vec, meta) in self.restore().items():
            store.add(id_, vec, meta)

    # ------------------------------------------------------------------
    def clear(self) -> None:
        self.client.delete(self.key)


class CycleCounterStore:
    """Persist chakra cycle counts in Redis or a JSON file."""

    def __init__(
        self,
        *,
        url: str = "redis://localhost:6379/0",
        key: str = "chakra_cycles",
        path: str | Path = "chakra_cycles.json",
        client: Any | None = None,
    ) -> None:
        self.key = key
        self.path = Path(path)
        self.client: Any | None = None
        if redis is not None:
            try:  # pragma: no cover - optional dependency
                self.client = client or redis.Redis.from_url(url)
                self.client.ping()
            except Exception:
                self.client = None

    # ------------------------------------------------------------------
    def load(self) -> Dict[str, int]:
        """Load cycle counts from Redis or the JSON file."""

        if self.client is not None:
            data = self.client.get(self.key)
            if data:
                return json.loads(data)
            return {}
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    # ------------------------------------------------------------------
    def save(self, counts: Dict[str, int]) -> None:
        """Persist cycle counts to Redis or the JSON file."""

        if self.client is not None:
            self.client.set(self.key, json.dumps(counts))
        else:
            self.path.write_text(json.dumps(counts), encoding="utf-8")

    # ------------------------------------------------------------------
    def increment(self, chakra: str) -> int:
        """Increment and persist the cycle count for ``chakra``.

        Returns the updated cycle identifier, allowing callers to track
        monotonically increasing heartbeat cycles across restarts.
        """

        counts = self.load()
        new_val = counts.get(chakra, 0) + 1
        counts[chakra] = new_val
        self.save(counts)
        return new_val


__all__ = ["DistributedMemory", "CycleCounterStore"]
