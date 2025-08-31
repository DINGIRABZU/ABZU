# pydocstyle: skip-file
"""Stub narrative memory engine.

Provides interfaces for recording story events composed of an actor,
action and symbolism.

Story text is persisted in a SQLite backend so narratives survive
process restarts and can be queried later.
"""

from __future__ import annotations

__version__ = "0.1.2"

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "narrative_engine.db"


@dataclass
class StoryEvent:
    """A story beat linking an actor, an action and optional symbolism."""

    actor: str
    action: str
    symbolism: str | None = None


class NarrativeEngine:
    """Interface for working with narrative story events."""

    def record(self, event: StoryEvent) -> None:
        """Record a story event in the narrative store."""
        raise NotImplementedError

    def stream(self) -> Iterable[StoryEvent]:
        """Iterate over stored story events."""
        raise NotImplementedError


def _get_conn() -> sqlite3.Connection:
    """Return connection to the story database, creating schema if needed."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS stories ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "text TEXT NOT NULL"
        ")"
    )
    return conn


def log_story(text: str) -> None:
    """Persist ``text`` to the story log."""

    with _get_conn() as conn:
        conn.execute("INSERT INTO stories (text) VALUES (?)", (text,))


def stream_stories() -> Iterable[str]:
    """Yield recorded stories in insertion order."""

    with _get_conn() as conn:
        for (text,) in conn.execute("SELECT text FROM stories ORDER BY id"):
            yield text


__all__ = [
    "StoryEvent",
    "NarrativeEngine",
    "log_story",
    "stream_stories",
    "DB_PATH",
]
