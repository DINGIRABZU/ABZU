from __future__ import annotations

"""Pluggable distributed memory with write-through replication."""

__version__ = "0.3.0"

import json
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

import tomllib

try:  # pragma: no cover - optional dependency
    import redis
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import boto3
except Exception:  # pragma: no cover - optional dependency
    boto3 = None  # type: ignore


# ---------------------------------------------------------------------------
class MemoryBackend:
    """Interface for persistence backends."""

    def backup(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def restore(
        self,
    ) -> Dict[str, Tuple[list[float], Dict[str, Any]]]:  # pragma: no cover - interface
        raise NotImplementedError

    def clear(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError


# ---------------------------------------------------------------------------
class RedisBackend(MemoryBackend):
    """Store vectors in a Redis hash."""

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        *,
        key: str = "vector_memory",
        client: Any | None = None,
    ) -> None:
        if redis is None:  # pragma: no cover - dependency check
            raise RuntimeError("redis package required for RedisBackend")
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
    def clear(self) -> None:
        self.client.delete(self.key)


# ---------------------------------------------------------------------------
class JSONBackend(MemoryBackend):
    """Persist vectors to a local JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    # ------------------------------------------------------------------
    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    # ------------------------------------------------------------------
    def backup(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:
        data = self._load()
        data[id_] = {"vector": list(vector), "metadata": metadata}
        self.path.write_text(json.dumps(data), encoding="utf-8")

    # ------------------------------------------------------------------
    def restore(self) -> Dict[str, Tuple[list[float], Dict[str, Any]]]:
        raw = self._load()
        return {k: (v["vector"], v["metadata"]) for k, v in raw.items()}

    # ------------------------------------------------------------------
    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


# ---------------------------------------------------------------------------
class S3Backend(MemoryBackend):
    """Persist vectors to S3 or MinIO."""

    def __init__(
        self,
        bucket: str,
        key: str,
        *,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        if boto3 is None:  # pragma: no cover - dependency check
            raise RuntimeError("boto3 package required for S3Backend")
        if client is None:
            client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
        self.client = client
        self.bucket = bucket
        self.key = key

    # ------------------------------------------------------------------
    def _load(self) -> Dict[str, Any]:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=self.key)
        except Exception:
            return {}
        body = obj["Body"].read()
        try:
            return json.loads(body)
        except Exception:
            return {}

    # ------------------------------------------------------------------
    def backup(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:
        data = self._load()
        data[id_] = {"vector": list(vector), "metadata": metadata}
        body = json.dumps(data).encode("utf-8")
        self.client.put_object(Bucket=self.bucket, Key=self.key, Body=body)

    # ------------------------------------------------------------------
    def restore(self) -> Dict[str, Tuple[list[float], Dict[str, Any]]]:
        raw = self._load()
        return {k: (v["vector"], v["metadata"]) for k, v in raw.items()}

    # ------------------------------------------------------------------
    def clear(self) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=self.key)
        except Exception:
            pass


# ---------------------------------------------------------------------------
def _backend_from_config(cfg: Dict[str, Any]) -> MemoryBackend:
    backend_type = cfg.get("type", "redis").lower()
    if backend_type == "redis":
        return RedisBackend(
            url=cfg.get("url", "redis://localhost:6379/0"),
            key=cfg.get("key", "vector_memory"),
        )
    if backend_type in {"json", "file"}:
        return JSONBackend(path=cfg["path"])
    if backend_type in {"s3", "minio"}:
        return S3Backend(
            bucket=cfg["bucket"],
            key=cfg.get("key", "vector_memory.json"),
            endpoint=cfg.get("endpoint"),
            access_key=cfg.get("access_key"),
            secret_key=cfg.get("secret_key"),
        )
    raise ValueError(f"Unknown backend type: {backend_type}")


# ---------------------------------------------------------------------------
class DistributedMemory:
    """Replicate writes to a primary backend with optional fallback."""

    def __init__(
        self, primary: MemoryBackend, fallback: MemoryBackend | None = None
    ) -> None:
        self.primary = primary
        self.fallback = fallback

    # ------------------------------------------------------------------
    @classmethod
    def from_config(
        cls, path: str | Path = Path("config/memory_backends.toml")
    ) -> "DistributedMemory":
        cfg = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        primary = _backend_from_config(cfg["primary"])
        fallback = _backend_from_config(cfg["fallback"]) if "fallback" in cfg else None
        return cls(primary, fallback)

    # ------------------------------------------------------------------
    def backup(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:
        self.primary.backup(id_, vector, metadata)
        if self.fallback is not None:
            try:  # pragma: no cover - best effort replication
                self.fallback.backup(id_, vector, metadata)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def restore(self) -> Dict[str, Tuple[list[float], Dict[str, Any]]]:
        try:
            data = self.primary.restore()
        except Exception:
            data = {}
        if data:
            return data
        if self.fallback is not None:
            return self.fallback.restore()
        return data

    # ------------------------------------------------------------------
    def restore_to(self, store: Any) -> None:
        for id_, (vec, meta) in self.restore().items():
            store.add(id_, vec, meta)

    # ------------------------------------------------------------------
    def clear(self) -> None:
        try:
            self.primary.clear()
        except Exception:
            pass
        if self.fallback is not None:
            try:
                self.fallback.clear()
            except Exception:
                pass


# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
class HeartbeatTimestampStore:
    """Persist last heartbeat timestamps in Redis or a JSON file."""

    def __init__(
        self,
        *,
        url: str = "redis://localhost:6379/0",
        key: str = "heartbeat_timestamps",
        path: str | Path = "heartbeat_timestamps.json",
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
    def load(self) -> Dict[str, float]:
        """Load heartbeat timestamps from Redis or the JSON file."""

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
    def save(self, beats: Dict[str, float]) -> None:
        """Persist heartbeat timestamps to Redis or the JSON file."""

        if self.client is not None:
            self.client.set(self.key, json.dumps(beats))
        else:
            self.path.write_text(json.dumps(beats), encoding="utf-8")

    # ------------------------------------------------------------------
    def update(self, component: str, timestamp: float) -> None:
        """Update and persist the heartbeat for ``component``."""

        beats = self.load()
        beats[component] = timestamp
        self.save(beats)


__all__ = [
    "MemoryBackend",
    "RedisBackend",
    "JSONBackend",
    "S3Backend",
    "DistributedMemory",
    "CycleCounterStore",
    "HeartbeatTimestampStore",
]
