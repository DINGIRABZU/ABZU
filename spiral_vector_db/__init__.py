from __future__ import annotations

"""Simple wrapper around ChromaDB for storing text embeddings."""

from pathlib import Path
from typing import Iterable, Any, Dict
import os
import uuid

import numpy as np

try:  # pragma: no cover - optional dependency
    import chromadb
    from chromadb.api import Collection
except Exception:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore
    Collection = object  # type: ignore

from MUSIC_FOUNDATION import qnl_utils

_DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "spiral_vector_db"
DB_PATH = Path(os.getenv("SPIRAL_VECTOR_PATH", str(_DEFAULT_PATH)))

_COLLECTION_NAME = "spiral_vectors"
_COLLECTION: Collection | None = None


def init_db(path: Path | None = None) -> Collection:
    """Return a persistent Chroma collection stored under ``path``."""
    if chromadb is None:  # pragma: no cover - optional dependency
        raise RuntimeError("chromadb library not installed")
    global _COLLECTION, DB_PATH
    if path is not None:
        DB_PATH = path
    if _COLLECTION is None:
        DB_PATH.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(DB_PATH))
        _COLLECTION = client.get_or_create_collection(_COLLECTION_NAME)
    return _COLLECTION


def _get_collection() -> Collection:
    if _COLLECTION is None:
        return init_db()
    return _COLLECTION


def insert_embeddings(data: Iterable[dict]) -> None:
    """Add ``data`` items with precomputed embeddings to the database."""
    items = list(data)
    if not items:
        return
    col = _get_collection()
    ids = []
    embeddings = []
    metadatas = []
    for item in items:
        ids.append(item.get("id", uuid.uuid4().hex))
        emb = item.get("embedding")
        if emb is None:
            emb = qnl_utils.quantum_embed(item.get("text", ""))
        emb = np.asarray(emb, dtype=float).tolist()
        embeddings.append(emb)
        meta = {k: v for k, v in item.items() if k not in {"embedding", "id"}}
        metadatas.append(meta)
    col.add(ids=ids, embeddings=embeddings, metadatas=metadatas)


def query_embeddings(text: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
    """Return ``top_k`` matches for ``text`` ordered by cosine similarity."""
    qvec = np.asarray(qnl_utils.quantum_embed(text), dtype=float)
    col = _get_collection()
    res = col.query(query_embeddings=[qvec.tolist()], n_results=max(top_k * 5, top_k))
    metas = res.get("metadatas", [[]])[0]
    embs = [np.asarray(e, dtype=float) for e in res.get("embeddings", [[]])[0]]

    results: list[dict] = []
    for emb, meta in zip(embs, metas):
        if filters is not None:
            skip = False
            for key, val in filters.items():
                if meta.get(key) != val:
                    skip = True
                    break
            if skip:
                continue
        if getattr(emb, "size", len(emb)) == 0:
            continue
        dot = sum(float(a) * float(b) for a, b in zip(emb, qvec))
        sim = float(dot / ((np.linalg.norm(emb) * np.linalg.norm(qvec)) + 1e-8))
        rec = dict(meta)
        rec["score"] = sim
        results.append(rec)
    results.sort(key=lambda m: m.get("score", 0.0), reverse=True)
    return results[:top_k]


__all__ = ["init_db", "insert_embeddings", "query_embeddings", "DB_PATH"]
