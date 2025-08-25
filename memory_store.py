"""FAISS-backed in-memory vector store with SQLite persistence."""

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
        if faiss is None or np is None:  # pragma: no cover - dependency check
            raise RuntimeError("faiss and numpy are required for MemoryStore")
        self.db_path = Path(db_path)
        self._pool_size = pool_size
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute(
                (
                    "CREATE TABLE IF NOT EXISTS memory (id TEXT PRIMARY KEY, "
                    "vector BLOB, metadata TEXT)"
                )
            )
            self._pool.put(conn)
        self._lock = threading.RLock()
        self.ids: List[str] = []
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.index: faiss.Index | None = None
        self.snapshot_interval = max(0, snapshot_interval)
        self._op_count = 0
        self.snapshot_dir = self.db_path.parent / "snapshots"
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
    def _load(self) -> None:
        with self._lock:
            with self._connection() as conn:
                cur = conn.execute("SELECT id, vector, metadata FROM memory")
                rows = cur.fetchall()
            self.ids = []
            self.metadata = {}
            if not rows:
                self.index = None
                return
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

    # ------------------------------------------------------------------
    def add(self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]) -> None:
        with self._lock:
            if self.index is None:
                self.index = faiss.IndexFlatL2(len(vector))
            vec = np.asarray(vector, dtype="float32")
            self.index.add(vec[None, :])
            self.ids.append(id_)
            self.metadata[id_] = dict(metadata)
            with self._connection() as conn:
                conn.execute(
                    (
                        "INSERT OR REPLACE INTO memory (id, vector, metadata) "
                        "VALUES (?, ?, ?)"
                    ),
                    (id_, vec.tobytes(), json.dumps(metadata)),
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
            if self.index is None or not self.ids:
                return []
            vec = np.asarray(vector, dtype="float32")[None, :]
            k = min(k, len(self.ids))
            distances, indices = self.index.search(vec, k)
            results: List[Tuple[str, List[float], Dict[str, Any]]] = []
            for idx in indices[0]:
                if idx == -1:
                    continue
                id_ = self.ids[int(idx)]
                emb = self.index.reconstruct(int(idx)).tolist()
                meta = dict(self.metadata.get(id_, {}))
                results.append((id_, emb, meta))
            return results

    # ------------------------------------------------------------------
    def rewrite(
        self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]
    ) -> None:
        with self._lock:
            vec = np.asarray(vector, dtype="float32")
            with self._connection() as conn:
                conn.execute(
                    (
                        "INSERT OR REPLACE INTO memory (id, vector, metadata) "
                        "VALUES (?, ?, ?)"
                    ),
                    (id_, vec.tobytes(), json.dumps(metadata)),
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
                conn.execute(
                    (
                        "CREATE TABLE IF NOT EXISTS memory (id TEXT PRIMARY KEY, "
                        "vector BLOB, metadata TEXT)"
                    )
                )
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
