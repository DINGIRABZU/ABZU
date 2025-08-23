"""Redis-backed helper for off-box vector memory backups."""
from __future__ import annotations

import json
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
    def backup(self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]) -> None:
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


__all__ = ["DistributedMemory"]
