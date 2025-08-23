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

    def __init__(self, db_path: str | Path, pool_size: int = 5):
        if faiss is None or np is None:  # pragma: no cover - dependency check
            raise RuntimeError("faiss and numpy are required for MemoryStore")
        self.db_path = Path(db_path)
        self._pool_size = pool_size
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS memory (id TEXT PRIMARY KEY, vector BLOB, metadata TEXT)"
            )
            self._pool.put(conn)
        self._lock = threading.RLock()
        self.ids: List[str] = []
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.index: faiss.Index | None = None
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
                    "INSERT OR REPLACE INTO memory (id, vector, metadata) VALUES (?, ?, ?)",
                    (id_, vec.tobytes(), json.dumps(metadata)),
                )
                conn.commit()

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
                    "INSERT OR REPLACE INTO memory (id, vector, metadata) VALUES (?, ?, ?)",
                    (id_, vec.tobytes(), json.dumps(metadata)),
                )
                conn.commit()
            self._load()

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
                    "CREATE TABLE IF NOT EXISTS memory (id TEXT PRIMARY KEY, vector BLOB, metadata TEXT)"
                )
                self._pool.put(conn)
            self._load()


__all__ = ["MemoryStore"]
