# pydocstyle: skip-file
"""Persist and query emotional feature vectors in SQLite.

The module maintains a table ``emotion_log`` inside ``data/emotions.db``. Each
record stores a timestamp and an associated emotion feature vector.

``log_emotion`` accepts sequences of numbers. When the optional
``transformers`` or ``dlib`` packages are installed, non‑numeric inputs such as
raw images or audio can also be passed. They are converted to numeric feature
vectors using :class:`~transformers.AutoFeatureExtractor` or ``dlib``
respectively. Without these dependencies, passing a non‑sequence raises a
``TypeError``.
"""

from __future__ import annotations

__version__ = "0.1.1"

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from worlds.config_registry import register_path

from aspect_processor import analyze_emotional

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
DB_ENV_VAR = "EMOTION_DB_PATH"


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
        (
            "CREATE TABLE IF NOT EXISTS emotion_log (timestamp REAL NOT NULL, "
            "vector TEXT NOT NULL)"
        )
    )


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Return a connection to the emotion database.

    The path can be supplied via ``db_path`` or the ``EMOTION_DB_PATH``
    environment variable. When neither is provided the module default
    ``DB_PATH`` is used. Required directories are created automatically and the
    schema is ensured to exist.
    """

    path = Path(db_path or os.getenv(DB_ENV_VAR, DB_PATH))
    path.parent.mkdir(parents=True, exist_ok=True)
    register_path("emotional", str(path))
    conn = sqlite3.connect(path)
    _ensure_schema(conn)
    return conn


def _normalise(features: EmotionFeatures) -> List[float]:
    """Convert ``features`` into a list of floats.

    If ``features`` is not a basic sequence, available feature extractors are
    used to derive numeric vectors. Extraction attempts are made with
    ``transformers.AutoFeatureExtractor`` first and then ``dlib``. When no
    extractor can handle ``features`` a ``TypeError`` is raised.
    """

    try:
        return [float(v) for v in features]
    except Exception:
        if AutoFeatureExtractor is not None:
            extractor = AutoFeatureExtractor.from_pretrained(
                "hf-internal-testing/tiny-random-wav2vec2-feature-extractor"
            )
            extracted = extractor(features)
            if isinstance(extracted, dict):
                extracted = next(iter(extracted.values()))
            if hasattr(extracted, "ravel"):
                extracted = extracted.ravel()
            if hasattr(extracted, "tolist"):
                extracted = extracted.tolist()
            return [float(v) for v in extracted]
        if dlib is not None:
            try:
                vec = dlib.vector(features)
            except Exception as exc:  # pragma: no cover - unexpected extractor error
                raise TypeError("features must be compatible with dlib.vector") from exc
            return [float(v) for v in vec]
        raise TypeError("features must be a sequence of floats")


def log_emotion(
    features: EmotionFeatures,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Path | str | None = None,
) -> EmotionEntry:
    """Persist ``features`` and return the stored :class:`EmotionEntry`."""

    vector = _normalise(features)
    analyze_emotional(vector)
    timestamp = time.time()
    entry = EmotionEntry(timestamp=timestamp, vector=vector)
    own_conn = conn is None
    conn = conn or get_connection(db_path)
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
    window: int,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Path | str | None = None,
) -> List[EmotionEntry]:
    """Return logged entries from the last ``window`` seconds."""

    since = max(0.0, time.time() - float(window))
    own_conn = conn is None
    conn = conn or get_connection(db_path)
    try:
        cur = conn.execute(
            (
                "SELECT timestamp, vector FROM emotion_log WHERE timestamp >= ? "
                "ORDER BY timestamp ASC"
            ),
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
