"""FAISS/SQLite-backed text vector store with decay and operation logging.

Persists entries under ``settings.vector_db_path`` and logs to
``data/vector_memory.log`` on each modification. Includes narrative hooks so
vectors can reference story events for downstream retrieval."""

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
import sqlite3

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
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = cast(Any, None)

try:  # pragma: no cover - optional dependency
    from sklearn.cluster import KMeans
except Exception:  # pragma: no cover - optional dependency
    KMeans = cast(Any, None)

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


__version__ = VersionInfo(0, 1, 3)
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
_OP_COUNT = 0


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
    global _OP_COUNT
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
    if shards != _SHARDS or snapshot_interval != _SNAPSHOT_INTERVAL:
        _STORE = None
        _COLLECTION = None
    _SHARDS = max(1, shards)
    _SNAPSHOT_INTERVAL = max(1, snapshot_interval)
    _OP_COUNT = 0
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
                _STORE = _MemoryStore(
                    _DIR / "memory.sqlite", snapshot_interval=_SNAPSHOT_INTERVAL
                )
            if _DIST is not None and not getattr(_STORE, "ids", []):
                _DIST.restore_to(_STORE)
    return _STORE


def _get_collection() -> Any:
    """Return the active collection instance used for queries."""
    if _COLLECTION is not None:
        return _COLLECTION
    return _get_store()


def _vacuum_files() -> None:
    store = _get_store()
    paths: List[Path] = []
    if hasattr(store, "db_path"):
        paths.append(Path(getattr(store, "db_path")))
    if hasattr(store, "_stores"):
        for sub in getattr(store, "_stores", []):
            if hasattr(sub, "db_path"):
                paths.append(Path(getattr(sub, "db_path")))
    for path in paths:
        try:
            with sqlite3.connect(path) as conn:
                conn.execute("VACUUM")
        except Exception:  # pragma: no cover - best effort
            logger.exception("vacuum failed for %s", path)


def _after_write() -> None:
    global _OP_COUNT
    _OP_COUNT += 1
    if _OP_COUNT < _SNAPSHOT_INTERVAL:
        return
    _OP_COUNT = 0
    store = _get_store()
    snap_dir = _DIR / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    try:
        if hasattr(store, "_stores"):
            store.snapshot(snap_dir)
        else:
            store.snapshot(snap_dir / "memory.sqlite")
    except Exception:  # pragma: no cover - best effort
        logger.exception("snapshot failed")
    _vacuum_files()


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
    _after_write()


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
    _after_write()
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
        _after_write()


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

    snap_dir = _DIR / "snapshots"
    manifest = snap_dir / "manifest.json"
    snap_dir.mkdir(parents=True, exist_ok=True)
    try:
        entries = (
            json.loads(manifest.read_text(encoding="utf-8"))
            if manifest.exists()
            else []
        )
        path_str = str(path)
        if path_str not in entries:
            entries.append(path_str)
            manifest.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except Exception:  # pragma: no cover - best effort
        logger.exception("failed to update snapshot manifest")


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


def persist_snapshot() -> Path:
    """Write a timestamped snapshot and return its path."""

    store = _get_store()
    snap_dir = _DIR / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = (
        snap_dir / stamp if hasattr(store, "_stores") else snap_dir / f"{stamp}.sqlite"
    )
    snapshot(path)
    return path


def restore_latest_snapshot() -> bool:
    """Restore the most recent snapshot if available."""

    snap_dir = _DIR / "snapshots"
    if not snap_dir.exists():
        return False
    snaps = sorted(snap_dir.iterdir())
    if not snaps:
        return False
    try:
        restore(snaps[-1])
        return True
    except Exception:  # pragma: no cover - best effort
        logger.exception("failed to restore snapshot")
        return False


def cluster_vectors(k: int = 5, limit: int = 1000) -> List[Dict[str, Any]]:
    """Cluster stored vectors into ``k`` groups using FAISS or K-means."""

    store = _get_store()
    ids = list(store.metadata.keys())
    if np is None or not ids:
        return []
    limit = min(limit, len(ids))
    k = min(k, limit)
    if k <= 0 or limit <= 0:
        return []
    vectors: List[Any] = []
    for idx, id_ in enumerate(ids[:limit]):
        if hasattr(store, "index") and getattr(store, "index", None) is not None:
            vectors.append(store.index.reconstruct(idx))
        else:
            meta = store.metadata[id_]
            vectors.append(_EMBED(meta.get("text", "")))
    arr = np.asarray(vectors, dtype="float32")
    if faiss is not None:
        km = faiss.Kmeans(arr.shape[1], k, niter=20, verbose=False)
        km.train(arr)
        _, assign = km.index.search(arr, 1)
        labels = assign.ravel()
    elif KMeans is not None:  # pragma: no cover - fallback
        km = KMeans(n_clusters=k, n_init="auto", random_state=0)
        labels = km.fit_predict(arr)
    else:  # pragma: no cover - no backend
        raise RuntimeError("no clustering backend available")
    clusters: List[Dict[str, Any]] = []
    for idx in range(k):
        members = int(np.sum(labels == idx))
        if members:
            clusters.append({"cluster": int(idx), "count": members})
    return clusters


def persist_clusters(
    k: int = 5,
    limit: int = 1000,
    path: str | Path | None = None,
) -> Path:
    """Persist cluster statistics to ``path`` and return it."""

    snap_dir = _DIR / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    clusters = cluster_vectors(k=k, limit=limit)
    if path is None:
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        path = snap_dir / f"clusters-{stamp}.json"
    else:
        path = Path(path)
    path.write_text(json.dumps(clusters, indent=2), encoding="utf-8")

    manifest = snap_dir / "clusters_manifest.json"
    try:
        entries = (
            json.loads(manifest.read_text(encoding="utf-8"))
            if manifest.exists()
            else []
        )
        path_str = str(path)
        if path_str not in entries:
            entries.append(path_str)
            manifest.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except Exception:  # pragma: no cover - best effort
        logger.exception("failed to update cluster manifest")
    return path


def load_latest_clusters() -> List[Dict[str, Any]]:
    """Return the most recently persisted clusters if available."""

    snap_dir = _DIR / "snapshots"
    manifest = snap_dir / "clusters_manifest.json"
    if not manifest.exists():
        return []
    try:
        entries = json.loads(manifest.read_text(encoding="utf-8"))
        if not entries:
            return []
        latest = Path(entries[-1])
        return json.loads(latest.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover - best effort
        logger.exception("failed to load cluster manifest")
        return []


__all__ = [
    "add_vector",
    "search",
    "rewrite_vector",
    "query_vectors",
    "snapshot",
    "restore",
    "persist_snapshot",
    "restore_latest_snapshot",
    "persist_clusters",
    "load_latest_clusters",
    "configure",
    "add_vectors",
    "search_batch",
    "cluster_vectors",
    "LOG_FILE",
]
