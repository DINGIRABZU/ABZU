"""FAISS-backed in-memory vector store with SQLite persistence.

The store transparently falls back to a pure Python implementation when
optional dependencies such as ``faiss`` or ``numpy`` are unavailable.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from queue import Queue
from typing import Any, Dict, Iterator, List, Sequence, Tuple, cast

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = cast(Any, None)

try:  # pragma: no cover - optional dependency
    # ``faiss`` is optional and ships without type hints
    import faiss
except Exception:  # pragma: no cover - optional dependency
    faiss = cast(Any, None)


class MemoryStore:
    """Persist vectors in SQLite while enabling fast similarity search via FAISS."""

    def __init__(
        self,
        db_path: str | Path,
        pool_size: int = 5,
        *,
        snapshot_interval: int = 0,
    ) -> None:
        self.db_path = Path(db_path)
        self._pool_size = pool_size
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._ensure_schema(conn)
            self._pool.put(conn)
        self._lock = threading.RLock()
        self.ids: List[str] = []
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.index: faiss.Index | None = None
        self._vectors: List[List[float]] = []  # fallback storage when FAISS unavailable
        self.snapshot_interval = max(0, snapshot_interval)
        self._op_count = 0
        self.snapshot_dir = self.db_path.parent / "snapshots"
        self._use_faiss = faiss is not None and np is not None
        self._load()

    # ------------------------------------------------------------------
    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = self._pool.get()
        try:
            yield conn
        finally:
            self._pool.put(conn)

    # ------------------------------------------------------------------
    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        """Create tables and perform simple migrations."""

        conn.execute(
            (
                "CREATE TABLE IF NOT EXISTS memory (id TEXT PRIMARY KEY, "
                "vector BLOB, metadata TEXT)"
            )
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        cur = conn.execute("SELECT value FROM meta WHERE key='version'")
        row = cur.fetchone()
        version = int(row[0]) if row else 0
        if version < 1:
            # previous schema may have lacked the metadata column
            info = conn.execute("PRAGMA table_info(memory)").fetchall()
            cols = {c[1] for c in info}
            if "metadata" not in cols:
                conn.execute("ALTER TABLE memory ADD COLUMN metadata TEXT")
            conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('version', '1')"
            )
        conn.commit()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        with self._lock:
            with self._connection() as conn:
                cur = conn.execute("SELECT id, vector, metadata FROM memory")
                rows = cur.fetchall()
            self.ids = []
            self.metadata = {}
            self._vectors = []
            if not rows:
                self.index = None
                return
            if self._use_faiss:
                first = rows[0]
                vec = np.frombuffer(first[1], dtype="float32")
                self.index = faiss.IndexFlatL2(len(vec))
                vectors = [vec]
                self.ids.append(first[0])
                self.metadata[first[0]] = json.loads(first[2]) if first[2] else {}
                for id_, vec_blob, meta_json in rows[1:]:
                    v = np.frombuffer(vec_blob, dtype="float32")
                    vectors.append(v)
                    self.ids.append(id_)
                    self.metadata[id_] = json.loads(meta_json) if meta_json else {}
                self.index.add(np.vstack(vectors))
            else:
                for id_, vec_blob, meta_json in rows:
                    try:
                        vec = json.loads(vec_blob)
                    except Exception:
                        vec = []
                    self.ids.append(id_)
                    self._vectors.append([float(x) for x in vec])
                    self.metadata[id_] = json.loads(meta_json) if meta_json else {}

    # ------------------------------------------------------------------
    def add(self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]) -> None:
        with self._lock:
            self.ids.append(id_)
            self.metadata[id_] = dict(metadata)
            if self._use_faiss:
                if self.index is None:
                    self.index = faiss.IndexFlatL2(len(vector))
                vec = np.asarray(vector, dtype="float32")
                self.index.add(vec[None, :])
                vec_blob = vec.tobytes()
            else:
                vec_list = [float(x) for x in vector]
                self._vectors.append(vec_list)
                vec_blob = json.dumps(vec_list)
            with self._connection() as conn:
                conn.execute(
                    (
                        "INSERT OR REPLACE INTO memory (id, vector, metadata) "
                        "VALUES (?, ?, ?)"
                    ),
                    (id_, vec_blob, json.dumps(metadata)),
                )
                conn.commit()
            self._after_mutation()

    # ------------------------------------------------------------------
    def delete(self, ids: Sequence[str]) -> None:
        """Remove ``ids`` from the store."""
        if not ids:
            return
        with self._lock:
            marks = ",".join("?" for _ in ids)
            with self._connection() as conn:
                conn.execute(f"DELETE FROM memory WHERE id IN ({marks})", list(ids))
                conn.commit()
            self._load()
            self._after_mutation()

    # ------------------------------------------------------------------
    def search(
        self, vector: Sequence[float], k: int
    ) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        with self._lock:
            if not self.ids:
                return []
            k = min(k, len(self.ids))
            results: List[Tuple[str, List[float], Dict[str, Any]]] = []
            if self._use_faiss and self.index is not None:
                vec = np.asarray(vector, dtype="float32")[None, :]
                distances, indices = self.index.search(vec, k)
                for idx in indices[0]:
                    if idx == -1:
                        continue
                    id_ = self.ids[int(idx)]
                    emb = self.index.reconstruct(int(idx)).tolist()
                    meta = dict(self.metadata.get(id_, {}))
                    results.append((id_, emb, meta))
                return results
            # fallback search
            vec = [float(x) for x in vector]
            dists = [sum((a - b) ** 2 for a, b in zip(v, vec)) for v in self._vectors]
            idxs = sorted(range(len(dists)), key=lambda i: dists[i])[:k]
            for idx in idxs:
                id_ = self.ids[idx]
                emb = list(self._vectors[idx])
                meta = dict(self.metadata.get(id_, {}))
                results.append((id_, emb, meta))
            return results

    # ------------------------------------------------------------------
    def rewrite(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:
        with self._lock:
            if self._use_faiss:
                vec = np.asarray(vector, dtype="float32")
                vec_blob = vec.tobytes()
            else:
                vec = [float(x) for x in vector]
                vec_blob = json.dumps(vec)
            with self._connection() as conn:
                conn.execute(
                    (
                        "INSERT OR REPLACE INTO memory (id, vector, metadata) "
                        "VALUES (?, ?, ?)"
                    ),
                    (id_, vec_blob, json.dumps(metadata)),
                )
                conn.commit()
            self._load()
            self._after_mutation()

    # ------------------------------------------------------------------
    def snapshot(self, path: str | Path) -> None:
        with self._lock:
            with self._connection() as conn:
                conn.commit()
            shutil.copy(self.db_path, path)

    # ------------------------------------------------------------------
    def restore(self, path: str | Path) -> None:
        with self._lock:
            while not self._pool.empty():
                conn: sqlite3.Connection = self._pool.get()
                conn.close()
            shutil.copy(path, self.db_path)
            for _ in range(self._pool_size):
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self._ensure_schema(conn)
                self._pool.put(conn)
            self._load()

    # ------------------------------------------------------------------
    def _after_mutation(self) -> None:
        if self.snapshot_interval <= 0:
            return
        self._op_count += 1
        if self._op_count < self.snapshot_interval:
            return
        self._op_count = 0
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.snapshot(self.snapshot_dir / self.db_path.name)
        except Exception:
            pass


class ShardedMemoryStore:
    """Shard vectors across multiple :class:`MemoryStore` instances."""

    def __init__(
        self,
        base_path: str | Path,
        *,
        shards: int = 1,
        snapshot_interval: int = 100,
    ) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.shards = max(1, shards)
        self.snapshot_interval = max(1, snapshot_interval)
        self._stores = [
            MemoryStore(self.base_path / f"shard_{i}.sqlite")
            for i in range(self.shards)
        ]
        self._op_count = 0
        self.snapshot_dir = self.base_path / "snapshots"
        if self.snapshot_dir.exists():
            try:
                self.restore(self.snapshot_dir)
            except Exception:
                pass

    # ------------------------------------------------------------------
    @property
    def ids(self) -> List[str]:
        out: List[str] = []
        for store in self._stores:
            out.extend(store.ids)
        return out

    # ------------------------------------------------------------------
    @property
    def metadata(self) -> Dict[str, Dict[str, Any]]:
        meta: Dict[str, Dict[str, Any]] = {}
        for store in self._stores:
            meta.update(store.metadata)
        return meta

    # ------------------------------------------------------------------
    def _pick(self, id_: str) -> MemoryStore:
        idx = int(id_, 16) % self.shards
        return self._stores[idx]

    # ------------------------------------------------------------------
    def add(self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]) -> None:
        self._pick(id_).add(id_, vector, metadata)
        self._after_mutation()

    # ------------------------------------------------------------------
    def delete(self, ids: Sequence[str]) -> None:
        by_shard: Dict[int, List[str]] = {}
        for id_ in ids:
            idx = int(id_, 16) % self.shards
            by_shard.setdefault(idx, []).append(id_)
        for idx, id_list in by_shard.items():
            self._stores[idx].delete(id_list)
        self._after_mutation()

    # ------------------------------------------------------------------
    def search(
        self, vector: Sequence[float], k: int
    ) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        results: List[Tuple[str, List[float], Dict[str, Any]]] = []
        for store in self._stores:
            results.extend(store.search(vector, k))
        if len(results) <= k:
            return results
        return results[:k]

    # ------------------------------------------------------------------
    def rewrite(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:
        self._pick(id_).rewrite(id_, vector, metadata)
        self._after_mutation()

    # ------------------------------------------------------------------
    def snapshot(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        for i, store in enumerate(self._stores):
            store.snapshot(path / f"shard_{i}.sqlite")

    # ------------------------------------------------------------------
    def restore(self, path: str | Path) -> None:
        path = Path(path)
        for i, store in enumerate(self._stores):
            db = path / f"shard_{i}.sqlite"
            if db.exists():
                store.restore(db)

    # ------------------------------------------------------------------
    def _after_mutation(self) -> None:
        self._op_count += 1
        if self._op_count >= self.snapshot_interval:
            try:
                self.snapshot(self.snapshot_dir)
            finally:
                self._op_count = 0


__all__ = ["MemoryStore", "ShardedMemoryStore"]
