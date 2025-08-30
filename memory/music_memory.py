# pydocstyle: skip-file
"""Persistent store for music embedding vectors with emotion labels.

This module provides a minimal interface to record and query embedding vectors
for music snippets. Embeddings from models such as CLAP or
SentenceTransformer can be stored alongside arbitrary metadata and an emotion
label. The data is persisted in a local SQLite database so it survives between
runs and may be used for retrieval‑augmented generation or mixing decisions.
"""

from __future__ import annotations

__version__ = "0.1.1"

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

_DEFAULT_DB = Path("data/music_memory.db")


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the required table if it does not already exist."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            embedding BLOB NOT NULL,
            dim INTEGER NOT NULL,
            emotion TEXT,
            metadata TEXT
        )
        """
    )


def add_track(
    embedding: np.ndarray,
    metadata: Dict[str, Any],
    emotion: str,
    *,
    track_id: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> str:
    """Store ``embedding`` with ``metadata`` and ``emotion``.

    Parameters
    ----------
    embedding:
        Numerical vector describing the music fragment.
    metadata:
        Arbitrary additional information about the track.
    emotion:
        Label describing the emotional tone of the track.
    track_id:
        Optional identifier. A random UUID is generated when omitted.
    db_path:
        Optional path to the SQLite database. Defaults to ``data/music_memory.db``.

    Returns
    -------
    str
        The identifier under which the track was stored.
    """

    tid = track_id or uuid.uuid4().hex
    arr = np.asarray(embedding, dtype=np.float32).ravel()
    meta_json = json.dumps(metadata)
    path = db_path or _DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        _ensure_schema(conn)
        conn.execute(
            "INSERT OR REPLACE INTO tracks (id, embedding, dim, emotion, metadata)"
            " VALUES (?, ?, ?, ?, ?)",
            (tid, arr.tobytes(), arr.size, emotion, meta_json),
        )
        conn.commit()
    finally:
        conn.close()
    return tid


def query_tracks(
    embedding: np.ndarray,
    *,
    k: int = 5,
    emotion: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Return up to ``k`` tracks most similar to ``embedding``.

    Parameters
    ----------
    embedding:
        Query vector to search for similar items.
    k:
        Maximum number of results to return.
    emotion:
        Optional emotion label to filter tracks.
    db_path:
        Optional path to the SQLite database. Defaults to ``data/music_memory.db``.

    Returns
    -------
    List[Dict[str, Any]]
        Each result contains ``id``, ``emotion``, ``metadata`` and ``score``.
    """

    qvec = np.asarray(embedding, dtype=np.float32).ravel()
    path = db_path or _DEFAULT_DB
    conn = sqlite3.connect(path)
    try:
        _ensure_schema(conn)
        if emotion is None:
            rows = conn.execute(
                "SELECT id, embedding, dim, emotion, metadata FROM tracks"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, embedding, dim, emotion, metadata FROM tracks"
                " WHERE emotion = ?",
                (emotion,),
            ).fetchall()
    finally:
        conn.close()

    results: List[Dict[str, Any]] = []
    qnorm = np.linalg.norm(qvec) + 1e-8
    for rid, blob, dim, emo, meta_json in rows:
        emb = np.frombuffer(blob, dtype=np.float32)
        if emb.size != dim:
            continue
        score = float(emb @ qvec / ((np.linalg.norm(emb) + 1e-8) * qnorm))
        meta = json.loads(meta_json) if meta_json else {}
        results.append(
            {
                "id": rid,
                "emotion": emo,
                "metadata": meta,
                "score": score,
            }
        )
    results.sort(key=lambda m: m["score"], reverse=True)
    return results[:k]


__all__ = ["add_track", "query_tracks"]
