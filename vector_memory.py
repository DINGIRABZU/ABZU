"""FAISS/SQLite-backed text vector store with decay and operation logging.

Persists entries under ``settings.vector_db_path`` and logs to
``data/vector_memory.log`` on each modification."""

from __future__ import annotations

import json
import logging
import math
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, cast

from crown_config import settings
from MUSIC_FOUNDATION import qnl_utils

try:  # pragma: no cover - optional dependency
    from distributed_memory import DistributedMemory
except Exception:  # pragma: no cover - optional dependency
    DistributedMemory = cast(Any, None)

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = cast(Any, None)

try:  # pragma: no cover - optional dependency
    from memory_store import MemoryStore as _MemoryStore, ShardedMemoryStore
except Exception:  # pragma: no cover - optional dependency

    class _MemoryStoreStub:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            raise RuntimeError("memory_store backend unavailable")

    _MemoryStore = _MemoryStoreStub  # type: ignore[misc,assignment]
    ShardedMemoryStore = _MemoryStoreStub  # type: ignore[misc,assignment]


def _default_embed(text: str) -> Any:
    return qnl_utils.quantum_embed(text)


_DIR = Path(settings.vector_db_path)
_EMBED: Callable[[str], Any] = _default_embed

_DECAY_SECONDS = 86_400.0  # one day
_DECAY_STRATEGY = "exponential"

LOG_FILE = Path("data/vector_memory.log")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VersionInfo:
    """Semantic version information for :mod:`vector_memory`."""

    major: int
    minor: int
    patch: int


__version__ = VersionInfo(0, 1, 0)
_STORE: Any | None = None
_STORE_LOCK = threading.RLock()
_DIST: Any | None = None
_COLLECTION: Any | None = None
_SHARDS = 1
_SNAPSHOT_INTERVAL = 100
_COMPACTION_THREAD: threading.Thread | None = None
_COMPACTION_STOP = threading.Event()
_COMPACTION_INTERVAL = 0.0
_DECAY_THRESHOLD = 0.01


def configure(
    *,
    db_path: str | Path | None = None,
    embedder: Callable[[str], Any] | None = None,
    redis_url: str | None = None,
    redis_client: Any | None = None,
    shards: int = 1,
    snapshot_interval: int = 100,
    decay_strategy: str | None = None,
    decay_seconds: float | None = None,
    compaction_interval: float | None = None,
    decay_threshold: float | None = None,
) -> None:
    """Configure storage location, embedding and decay behaviour."""

    global _DIR, _EMBED, _STORE, _DIST, _COLLECTION, _SHARDS, _SNAPSHOT_INTERVAL
    global _DECAY_STRATEGY, _DECAY_SECONDS, _COMPACTION_INTERVAL, _DECAY_THRESHOLD
    if db_path is not None:
        _DIR = Path(db_path)
        _STORE = None
        _COLLECTION = None
    if embedder is not None:
        _EMBED = embedder
    if redis_url is not None or redis_client is not None:
        if DistributedMemory is None:
            raise RuntimeError("DistributedMemory backend unavailable")
        _DIST = DistributedMemory(
            redis_url or "redis://localhost:6379/0", client=redis_client
        )
    _SHARDS = max(1, shards)
    _SNAPSHOT_INTERVAL = max(1, snapshot_interval)
    if decay_strategy is not None:
        _DECAY_STRATEGY = decay_strategy
    if decay_seconds is not None:
        _DECAY_SECONDS = decay_seconds
    if compaction_interval is not None:
        _COMPACTION_INTERVAL = compaction_interval
        _DECAY_THRESHOLD = decay_threshold or _DECAY_THRESHOLD
        _start_compaction_thread()


def _log(op: str, text: str, meta: Dict[str, Any]) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": op,
            "text": text,
            "metadata": meta,
        }
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry))
            fh.write("\n")
    except Exception:  # pragma: no cover - safeguard
        logger.exception("failed to log vector_memory operation")


def _get_store() -> Any:
    """Return a persistent :class:`MemoryStore` instance."""
    if _MemoryStore is None:  # pragma: no cover - optional dependency
        raise RuntimeError("memory_store backend unavailable")
    global _STORE
    with _STORE_LOCK:
        if _STORE is None:
            _DIR.mkdir(parents=True, exist_ok=True)
            if _SHARDS > 1:
                _STORE = ShardedMemoryStore(
                    _DIR,
                    shards=_SHARDS,
                    snapshot_interval=_SNAPSHOT_INTERVAL,
                )
            else:
                _STORE = _MemoryStore(_DIR / "memory.sqlite")
            if _DIST is not None and not getattr(_STORE, "ids", []):
                _DIST.restore_to(_STORE)
    return _STORE


def _get_collection() -> Any:
    """Return the active collection instance used for queries."""
    if _COLLECTION is not None:
        return _COLLECTION
    return _get_store()


def add_vector(text: str, metadata: Dict[str, Any]) -> None:
    """Embed ``text`` and store it with ``metadata``."""
    meta = dict(metadata)
    meta.setdefault("text", text)
    meta.setdefault("timestamp", datetime.utcnow().isoformat())
    col = _get_collection()
    emb_raw = _EMBED(text)
    if np is not None:
        emb = np.asarray(emb_raw, dtype=float).tolist()
    else:
        emb = [float(x) for x in emb_raw]
    id_ = uuid.uuid4().hex
    try:
        col.add(id_, emb, meta)
    except Exception:
        logger.debug(
            "collection.add failed, retrying with legacy signature",
            exc_info=True,
        )
        col.add([id_], [emb], [meta])
    if _DIST is not None:
        try:
            _DIST.backup(id_, emb, meta)
        except Exception:  # pragma: no cover - best effort backup
            logger.exception("distributed backup failed for %s", id_)
    _log("add", text, meta)


def add_vectors(texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
    """Add multiple vectors in a batch."""
    for text, meta in zip(texts, metadatas):
        add_vector(text, meta)


def _decay(ts: str) -> float:
    try:
        t = datetime.fromisoformat(ts)
    except Exception:  # pragma: no cover - invalid timestamp
        return 1.0
    age = (datetime.utcnow() - t).total_seconds()
    if _DECAY_STRATEGY == "none":
        return 1.0
    if _DECAY_STRATEGY == "linear":
        return max(0.0, 1.0 - age / _DECAY_SECONDS)
    return math.exp(-age / _DECAY_SECONDS)


def search(
    query: str, filter: Optional[Dict[str, Any]] = None, *, k: int = 5
) -> List[Dict[str, Any]]:
    """Return ``k`` fuzzy matches for ``query`` ordered by decayed similarity."""

    qvec_raw = _EMBED(query)
    if np is not None:
        qvec = np.asarray(qvec_raw, dtype=float)
    else:
        qvec = [float(x) for x in qvec_raw]
    col = _get_collection()
    k_search = max(k * 5, k)
    results: List[Dict[str, Any]] = []
    qvec_list = qvec.tolist() if hasattr(qvec, "tolist") else list(qvec)
    if hasattr(col, "search"):
        raw = col.search(qvec_list, k=k_search)
        iterator: Iterable[tuple[Any, Any, Any]] = (
            (mid, emb, meta) for mid, emb, meta in raw
        )
    else:
        raw = col.query([qvec_list], n_results=k_search)
        iterator = zip(
            raw.get("ids", [[]])[0] if "ids" in raw else range(k_search),
            raw["embeddings"][0],
            raw["metadatas"][0],
        )
    for _id, emb_list, meta in iterator:
        if filter is not None:
            skip = False
            for key, val in filter.items():
                if meta.get(key) != val:
                    skip = True
                    break
            if skip:
                continue
        if np is not None:
            emb = np.asarray(emb_list, dtype=float)
            dot = float(emb @ qvec)
            norm_emb = float(np.linalg.norm(emb))
            norm_q = float(np.linalg.norm(qvec))
        else:
            emb = [float(x) for x in emb_list]
            dot = sum(float(a) * float(b) for a, b in zip(emb, qvec))
            norm_emb = math.sqrt(sum(float(x) ** 2 for x in emb))
            norm_q = math.sqrt(sum(float(x) ** 2 for x in qvec))
        if norm_emb == 0 or norm_q == 0:
            continue
        sim = float(dot / ((norm_emb * norm_q) + 1e-8))
        weight = _decay(meta.get("timestamp", ""))
        score = sim * weight
        out = dict(meta)
        out["score"] = score
        results.append(out)
    results.sort(key=lambda m: m.get("score", 0.0), reverse=True)
    return results[:k]


def search_batch(
    queries: List[str], filter: Optional[Dict[str, Any]] = None, *, k: int = 5
) -> List[List[Dict[str, Any]]]:
    """Search for multiple ``queries`` returning a list of result lists."""
    return [search(q, filter=filter, k=k) for q in queries]


def rewrite_vector(old_id: str, new_text: str) -> bool:
    """Replace the entry ``old_id`` with ``new_text`` preserving metadata.

    Returns ``True`` on success. If a failure occurs that prevents rewriting,
    the underlying exception is logged and re-raised so callers can react or
    retry.
    """
    store = _get_store()
    emb_raw = _EMBED(new_text)
    meta = dict(store.metadata.get(old_id, {}))
    meta.setdefault("timestamp", datetime.utcnow().isoformat())
    meta["text"] = new_text
    if np is not None:
        emb_list = np.asarray(emb_raw, dtype=float).tolist()
    else:
        emb_list = [float(x) for x in emb_raw]
    store.rewrite(old_id, emb_list, meta)
    if _DIST is not None:
        _DIST.backup(old_id, emb_list, meta)
    _log("rewrite", new_text, meta)
    return True


def query_vectors(
    filter: Optional[Dict[str, Any]] = None, *, limit: int = 10
) -> List[Dict[str, Any]]:
    """Return recent stored entries matching ``filter``."""
    store = _get_store()
    items: List[Dict[str, Any]] = []
    for id_, meta in store.metadata.items():
        if filter is not None:
            skip = False
            for key, val in filter.items():
                if meta.get(key) != val:
                    skip = True
                    break
            if skip:
                continue
        out = dict(meta)
        out["id"] = id_
        items.append(out)
    items.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
    return items[:limit]


def _compact(threshold: float) -> None:
    store = _get_store()
    stale: List[str] = []
    for id_, meta in store.metadata.items():
        if _decay(meta.get("timestamp", "")) < threshold:
            stale.append(id_)
    if stale:
        store.delete(stale)


def _compactor() -> None:
    while not _COMPACTION_STOP.is_set():
        try:
            _compact(_DECAY_THRESHOLD)
        except Exception:  # pragma: no cover - best effort
            logger.exception("compaction failed")
        if _COMPACTION_INTERVAL <= 0:
            break
        _COMPACTION_STOP.wait(_COMPACTION_INTERVAL)


def _start_compaction_thread() -> None:
    global _COMPACTION_THREAD
    if _COMPACTION_THREAD and _COMPACTION_THREAD.is_alive():
        return
    _COMPACTION_STOP.clear()
    t = threading.Thread(target=_compactor, name="vector_compactor", daemon=True)
    t.start()
    _COMPACTION_THREAD = t


def snapshot(path: str | Path) -> None:
    """Persist the current collection to ``path``."""

    col = _get_collection()
    if hasattr(col, "snapshot"):
        col.snapshot(path)
    else:
        data = col.get()
        Path(path).write_text(json.dumps(data), encoding="utf-8")


def restore(path: str | Path) -> None:
    """Load collection data from ``path`` replacing existing entries."""

    col = _get_collection()
    if hasattr(col, "restore"):
        col.restore(path)
    else:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        existing = col.get().get("ids", [])
        if existing:
            col.delete(existing)
        col.add(data["ids"], data["embeddings"], data["metadatas"])


__all__ = [
    "add_vector",
    "search",
    "rewrite_vector",
    "query_vectors",
    "snapshot",
    "restore",
    "configure",
    "add_vectors",
    "search_batch",
    "LOG_FILE",
]
