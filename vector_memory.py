from __future__ import annotations

"""Lightweight text vector memory built on ChromaDB.

The database location defaults to ``data/vector_memory`` next to this file but
can be overridden by setting the ``VECTOR_DB_PATH`` environment variable.  Each
stored entry is timestamped so query results decay in relevance over time.
"""

import json
import logging
import math
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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

from crown_config import settings
from MUSIC_FOUNDATION import qnl_utils

_DIR = Path(settings.vector_db_path)

_COLLECTION_NAME = "memory"
_DECAY_SECONDS = 86_400.0  # one day

LOG_FILE = Path("data/vector_memory.log")
logger = logging.getLogger(__name__)

_COLLECTION: Collection | None = None


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


def _get_collection() -> Collection:
    """Return a persistent Chroma collection."""
    if chromadb is None:  # pragma: no cover - optional dependency
        raise RuntimeError("chromadb library not installed")
    global _COLLECTION
    if _COLLECTION is None:
        _DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(_DIR))
        _COLLECTION = client.get_or_create_collection(_COLLECTION_NAME)
    return _COLLECTION


def add_vector(text: str, metadata: Dict[str, Any]) -> None:
    """Embed ``text`` and store it with ``metadata``."""
    meta = dict(metadata)
    meta.setdefault("text", text)
    meta.setdefault("timestamp", datetime.utcnow().isoformat())
    col = _get_collection()
    emb_raw = qnl_utils.quantum_embed(text)
    if np is not None:
        emb = np.asarray(emb_raw, dtype=float).tolist()
    else:
        emb = [float(x) for x in emb_raw]
    col.add(
        ids=[uuid.uuid4().hex],
        embeddings=[emb],
        metadatas=[meta],
    )
    _log("add", text, meta)


def _decay(ts: str) -> float:
    try:
        t = datetime.fromisoformat(ts)
    except Exception:  # pragma: no cover - invalid timestamp
        return 1.0
    age = (datetime.utcnow() - t).total_seconds()
    return math.exp(-age / _DECAY_SECONDS)


def search(
    query: str, filter: Optional[Dict[str, Any]] = None, *, k: int = 5
) -> List[Dict[str, Any]]:
    """Return ``k`` fuzzy matches for ``query`` ordered by decayed similarity."""

    qvec_raw = qnl_utils.quantum_embed(query)
    if np is not None:
        qvec = np.asarray(qvec_raw, dtype=float)
    else:
        qvec = [float(x) for x in qvec_raw]
    col = _get_collection()
    res = col.query(query_embeddings=[list(qvec)], n_results=max(k * 5, k))
    metas = res.get("metadatas", [[]])[0]
    if np is not None:
        embs = [np.asarray(e, dtype=float) for e in res.get("embeddings", [[]])[0]]
    else:
        embs = [[float(x) for x in e] for e in res.get("embeddings", [[]])[0]]

    results: List[Dict[str, Any]] = []
    for emb, meta in zip(embs, metas):
        if filter is not None:
            skip = False
            for key, val in filter.items():
                if meta.get(key) != val:
                    skip = True
                    break
            if skip:
                continue
        if getattr(emb, "size", len(emb)) == 0:
            continue
        if np is not None:
            dot = float(emb @ qvec)
            norm_emb = float(np.linalg.norm(emb))
            norm_q = float(np.linalg.norm(qvec))
        else:
            dot = sum(float(a) * float(b) for a, b in zip(emb, qvec))
            norm_emb = math.sqrt(sum(float(x) ** 2 for x in emb))
            norm_q = math.sqrt(sum(float(x) ** 2 for x in qvec))
        sim = float(dot / ((norm_emb * norm_q) + 1e-8))
        weight = _decay(meta.get("timestamp", ""))
        score = sim * weight
        out = dict(meta)
        out["score"] = score
        results.append(out)

    results.sort(key=lambda m: m.get("score", 0.0), reverse=True)
    return results[:k]


def rewrite_vector(old_id: str, new_text: str) -> bool:
    """Replace the entry ``old_id`` with ``new_text`` preserving metadata.

    Returns ``True`` on success. If a failure occurs that prevents rewriting,
    the underlying exception is logged and re-raised so callers can react or
    retry.
    """
    col = _get_collection()
    emb_raw = qnl_utils.quantum_embed(new_text)
    try:
        rec = col.get(ids=[old_id])
        meta_list = rec.get("metadatas", [[]])[0]
        meta = meta_list[0] if meta_list else {}
    except Exception:
        meta = {}
    meta.setdefault("timestamp", datetime.utcnow().isoformat())
    meta["text"] = new_text
    try:
        if np is not None:
            emb_list = np.asarray(emb_raw, dtype=float).tolist()
        else:
            emb_list = [float(x) for x in emb_raw]
        col.update(ids=[old_id], embeddings=[emb_list], metadatas=[meta])
    except Exception:
        try:
            col.delete(ids=[old_id])
        except Exception:
            logger.exception("Failed to delete vector %s", old_id)
            raise
        try:
            col.add(ids=[old_id], embeddings=[emb_list], metadatas=[meta])
        except Exception:
            logger.exception("Failed to add vector %s during rewrite", old_id)
            raise
    _log("rewrite", new_text, meta)
    return True


def query_vectors(
    filter: Optional[Dict[str, Any]] = None, *, limit: int = 10
) -> List[Dict[str, Any]]:
    """Return recent stored entries matching ``filter``."""
    return search("", filter=filter, k=limit)


__all__ = [
    "add_vector",
    "search",
    "rewrite_vector",
    "query_vectors",
    "LOG_FILE",
]
