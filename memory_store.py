"""FAISS-backed in-memory vector store with SQLite persistence."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None  # type: ignore


class MemoryStore:
    """Persist vectors in SQLite while enabling fast similarity search via FAISS."""

    def __init__(self, db_path: str | Path):
        if faiss is None or np is None:  # pragma: no cover - dependency check
            raise RuntimeError("faiss and numpy are required for MemoryStore")
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memory (id TEXT PRIMARY KEY, vector BLOB, metadata TEXT)"
        )
        self.ids: List[str] = []
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.index: faiss.Index | None = None
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        cur = self.conn.execute("SELECT id, vector, metadata FROM memory")
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
        if self.index is None:
            self.index = faiss.IndexFlatL2(len(vector))
        vec = np.asarray(vector, dtype="float32")
        self.index.add(vec[None, :])
        self.ids.append(id_)
        self.metadata[id_] = dict(metadata)
        self.conn.execute(
            "INSERT OR REPLACE INTO memory (id, vector, metadata) VALUES (?, ?, ?)",
            (id_, vec.tobytes(), json.dumps(metadata)),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    def search(self, vector: Sequence[float], k: int) -> List[Tuple[str, List[float], Dict[str, Any]]]:
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
    def rewrite(self, id_: str, vector: Sequence[float], metadata: Dict[str, Any]) -> None:
        vec = np.asarray(vector, dtype="float32")
        self.conn.execute(
            "INSERT OR REPLACE INTO memory (id, vector, metadata) VALUES (?, ?, ?)",
            (id_, vec.tobytes(), json.dumps(metadata)),
        )
        self.conn.commit()
        self._load()

    # ------------------------------------------------------------------
    def snapshot(self, path: str | Path) -> None:
        self.conn.commit()
        shutil.copy(self.db_path, path)

    # ------------------------------------------------------------------
    def restore(self, path: str | Path) -> None:
        self.conn.close()
        shutil.copy(path, self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._load()


__all__ = ["MemoryStore"]
