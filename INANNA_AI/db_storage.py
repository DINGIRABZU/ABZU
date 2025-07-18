"""SQLite helpers to store voice interactions."""
from __future__ import annotations

import sqlite3
from datetime import datetime
import json
from pathlib import Path
from typing import List, Dict, Optional, Any

DB_PATH = Path(__file__).resolve().parent / "interactions.db"


def init_db(db_path: Path = DB_PATH) -> None:
    """Create the interactions table if it does not exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                transcript TEXT NOT NULL,
                emotion TEXT NOT NULL,
                response_path TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                response_time REAL NOT NULL,
                coherence REAL NOT NULL,
                relevance REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_profiles (
                emotion TEXT PRIMARY KEY,
                params TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                emotion TEXT NOT NULL,
                satisfaction REAL NOT NULL,
                ethical_alignment REAL NOT NULL,
                existential_clarity REAL NOT NULL
            )
            """
        )
    conn.close()


def save_interaction(
    transcript: str,
    emotion: str,
    response_path: str,
    *,
    db_path: Path = DB_PATH,
) -> None:
    """Record a conversation entry in the database."""
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            "INSERT INTO interactions(timestamp, transcript, emotion, response_path) VALUES (?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), transcript, emotion, response_path),
        )
    conn.close()


def log_benchmark(
    model: str,
    response_time: float,
    coherence: float,
    relevance: float,
    *,
    db_path: Path = DB_PATH,
) -> None:
    """Record model metrics in the database."""
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            "INSERT INTO benchmarks(timestamp, model, response_time, coherence, relevance) VALUES (?, ?, ?, ?, ?)",
            (
                datetime.utcnow().isoformat(),
                model,
                response_time,
                coherence,
                relevance,
            ),
        )
    conn.close()


def log_feedback(
    emotion: str,
    satisfaction: float,
    ethical_alignment: float,
    existential_clarity: float,
    *,
    db_path: Path = DB_PATH,
) -> None:
    """Record user feedback in the database."""
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            "INSERT INTO feedback(timestamp, emotion, satisfaction, ethical_alignment, existential_clarity)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                datetime.utcnow().isoformat(),
                emotion,
                satisfaction,
                ethical_alignment,
                existential_clarity,
            ),
        )
    conn.close()


def save_voice_profiles(
    profiles: Dict[str, Dict[str, float]], *, db_path: Path = DB_PATH
) -> None:
    """Persist voice style parameters to ``db_path``."""
    conn = sqlite3.connect(db_path)
    with conn:
        for emotion, params in profiles.items():
            conn.execute(
                "INSERT INTO voice_profiles(emotion, params) VALUES (?, ?) "
                "ON CONFLICT(emotion) DO UPDATE SET params=excluded.params",
                (emotion, json.dumps(params)),
            )
    conn.close()


def fetch_voice_profiles(db_path: Path = DB_PATH) -> Dict[str, Dict[str, float]]:
    """Return stored voice profiles keyed by emotion."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT emotion, params FROM voice_profiles")
    rows = cur.fetchall()
    conn.close()
    return {row[0]: json.loads(row[1]) for row in rows}


def fetch_benchmarks(limit: Optional[int] = None, db_path: Path = DB_PATH) -> List[Dict[str, float | str]]:
    """Return recorded benchmark metrics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = "SELECT timestamp, model, response_time, coherence, relevance FROM benchmarks ORDER BY id DESC"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "timestamp": row[0],
            "model": row[1],
            "response_time": row[2],
            "coherence": row[3],
            "relevance": row[4],
        }
        for row in rows
    ]


def fetch_feedback(
    limit: Optional[int] = None, db_path: Path = DB_PATH
) -> List[Dict[str, Any]]:
    """Return feedback entries ordered from newest to oldest."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = (
        "SELECT timestamp, emotion, satisfaction, ethical_alignment, "
        "existential_clarity FROM feedback ORDER BY id DESC"
    )
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "timestamp": row[0],
            "emotion": row[1],
            "satisfaction": row[2],
            "ethical_alignment": row[3],
            "existential_clarity": row[4],
        }
        for row in rows
    ]


def fetch_interactions(limit: Optional[int] = None, db_path: Path = DB_PATH) -> List[Dict[str, str]]:
    """Return saved interactions ordered from newest to oldest."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = "SELECT timestamp, transcript, emotion, response_path FROM interactions ORDER BY id DESC"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "timestamp": row[0],
            "transcript": row[1],
            "emotion": row[2],
            "response_path": row[3],
        }
        for row in rows
    ]


def last_interaction(db_path: Path = DB_PATH) -> Optional[Dict[str, str]]:
    """Return the most recent interaction or ``None`` if database is empty."""
    rows = fetch_interactions(limit=1, db_path=db_path)
    return rows[0] if rows else None


__all__ = [
    "init_db",
    "save_interaction",
    "fetch_interactions",
    "last_interaction",
    "log_benchmark",
    "fetch_benchmarks",
    "log_feedback",
    "fetch_feedback",
    "save_voice_profiles",
    "fetch_voice_profiles",
]
