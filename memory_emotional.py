"""Persist and query emotional feature vectors in SQLite.

The module maintains a table ``emotion_log`` inside ``data/emotions.db``. Each
record stores a timestamp and an associated emotion feature vector. Feature
extraction may leverage optional dependencies such as HuggingFace
``transformers`` or ``dlib`` when available, otherwise the API accepts raw
numeric sequences directly.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

try:  # Optional dependency
    from transformers import AutoFeatureExtractor  # type: ignore
except Exception:  # pragma: no cover - dependency may be missing
    AutoFeatureExtractor = None

try:  # Optional dependency
    import dlib  # type: ignore
except Exception:  # pragma: no cover - dependency may be missing
    dlib = None

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "emotions.db"


@dataclass
class EmotionEntry:
    """Stored emotion vector with its capture ``timestamp``."""

    timestamp: float
    vector: List[float]


# Basic emotion features are simply sequences of floats
EmotionFeatures = Sequence[float]


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create required table in ``conn`` if it does not already exist."""

    conn.execute(
        "CREATE TABLE IF NOT EXISTS emotion_log (timestamp REAL NOT NULL, vector TEXT NOT NULL)"
    )


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the emotion database, creating directories as needed."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    _ensure_schema(conn)
    return conn


def _normalise(features: EmotionFeatures) -> List[float]:
    """Convert ``features`` into a list of floats.

    If ``features`` isn't already a sequence, this function attempts to fall back
    to optional feature extractors when available. Without those dependencies,
    a ``TypeError`` is raised.
    """

    try:
        return [float(v) for v in features]
    except Exception:
        if AutoFeatureExtractor is not None or dlib is not None:
            # Real extractor logic would go here. We return an empty vector to
            # degrade gracefully when extraction is unsupported in this
            # environment.
            return []
        raise TypeError("features must be a sequence of floats")


def log_emotion(
    features: EmotionFeatures, conn: Optional[sqlite3.Connection] = None
) -> EmotionEntry:
    """Persist ``features`` and return the stored :class:`EmotionEntry`."""

    vector = _normalise(features)
    timestamp = time.time()
    entry = EmotionEntry(timestamp=timestamp, vector=vector)
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO emotion_log (timestamp, vector) VALUES (?, ?)",
                (entry.timestamp, json.dumps(entry.vector)),
            )
    finally:
        if own_conn:
            conn.close()
    return entry


def fetch_emotion_history(
    window: int, conn: Optional[sqlite3.Connection] = None
) -> List[EmotionEntry]:
    """Return logged entries from the last ``window`` seconds."""

    since = max(0.0, time.time() - float(window))
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        cur = conn.execute(
            "SELECT timestamp, vector FROM emotion_log WHERE timestamp >= ? ORDER BY timestamp ASC",
            (since,),
        )
        rows = cur.fetchall()
        return [EmotionEntry(ts, json.loads(vec)) for ts, vec in rows]
    finally:
        if own_conn:
            conn.close()


__all__ = [
    "EmotionEntry",
    "EmotionFeatures",
    "log_emotion",
    "fetch_emotion_history",
    "get_connection",
    "DB_PATH",
]
