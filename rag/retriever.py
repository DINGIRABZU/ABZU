from __future__ import annotations

"""Query Chroma collections using a shared embedding model."""

from pathlib import Path
from typing import List, Dict, Any
import logging
import math

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import chromadb
    from chromadb.api import Collection
except Exception:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore
    Collection = object  # type: ignore

from . import embedder as rag_embedder
from INANNA_AI.utils import sentiment_score
from memory import spiral_cortex

_DB_DIR = Path("data") / "crown_queries"
_COLLECTION_CACHE: dict[str, Collection] = {}

logger = logging.getLogger(__name__)


def get_collection(name: str) -> Collection:
    """Return Chroma collection ``name`` stored under :data:`_DB_DIR`."""
    if chromadb is None:  # pragma: no cover - optional dependency
        raise RuntimeError("chromadb library not installed")
    col = _COLLECTION_CACHE.get(name)
    if col is None:
        _DB_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(_DB_DIR))
        col = client.get_or_create_collection(name)
        _COLLECTION_CACHE[name] = col
    return col


def retrieve_top(question: str, top_n: int = 5, *, collection: str = "tech") -> List[Dict[str, Any]]:
    """Return ranked snippets for ``question`` from ``collection``."""
    model = rag_embedder._get_model()
    q_raw = model.encode([question])[0]
    if np is not None:
        query_emb = np.asarray(q_raw, dtype=float)
    else:
        query_emb = [float(x) for x in q_raw]
    col = get_collection(collection)
    res = col.query(query_embeddings=[list(query_emb)], n_results=max(top_n * 5, top_n))
    metas = res.get("metadatas", [[]])[0]
    if np is not None:
        embs = [np.asarray(e, dtype=float) for e in res.get("embeddings", [[]])[0]]
    else:
        embs = [[float(x) for x in e] for e in res.get("embeddings", [[]])[0]]
    results: list[Dict[str, Any]] = []
    for emb, meta in zip(embs, metas):
        if getattr(emb, "size", len(emb)) == 0:
            continue
        if np is not None:
            dot = float(emb @ query_emb)
            norm_emb = float(np.linalg.norm(emb))
            norm_q = float(np.linalg.norm(query_emb))
        else:
            dot = sum(float(a) * float(b) for a, b in zip(emb, query_emb))
            norm_emb = math.sqrt(sum(float(x) ** 2 for x in emb))
            norm_q = math.sqrt(sum(float(x) ** 2 for x in query_emb))
        sim = float(dot / ((norm_emb * norm_q) + 1e-8))
        rec = dict(meta)
        rec["score"] = sim
        results.append(rec)
    results.sort(key=lambda m: m.get("score", 0.0), reverse=True)
    top = results[:top_n]

    try:
        sent = sentiment_score(question)
        spiral_cortex.log_insight(question, top, sent)
    except Exception:
        logger.exception("failed to log retrieval")

    return top


__all__ = ["retrieve_top", "get_collection"]
