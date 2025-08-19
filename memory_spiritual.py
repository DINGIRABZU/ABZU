"""SQLite-backed event ↔ symbol memory.

On import the module ensures ``data/ontology.db`` exists, creating it from
``data/ontology_schema.sql`` if necessary. This keeps the ontology database
out of version control while providing a lightweight persistent mapping.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Optional

from aspect_processor import analyze_phonetic, analyze_semantic

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "ontology.db"
SCHEMA_PATH = BASE_DIR / "data" / "ontology_schema.sql"


def init_db(conn: sqlite3.Connection) -> None:
    """Initialise the database schema for ``conn``."""

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)


def _ensure_db_file() -> None:
    """Create the ontology database if it does not exist."""

    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        try:
            init_db(conn)
        finally:
            conn.close()


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection, initialising schema if required."""

    path_str = str(db_path)
    is_memory = path_str == ":memory:" or path_str.startswith("file::memory:")
    conn = sqlite3.connect(path_str, uri=path_str.startswith("file:"))
    if is_memory or not Path(path_str).exists():
        init_db(conn)
    return conn


def set_event_symbol(
    event: str, symbol: str, conn: Optional[sqlite3.Connection] = None
) -> None:
    """Store or update the symbol associated with ``event``."""

    analyze_phonetic(event)
    analyze_semantic(symbol)
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO event_symbol (event, symbol) VALUES (?, ?)",
                (event, symbol),
            )
    finally:
        if own_conn:
            conn.close()


def get_event_symbol(
    event: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[str]:
    """Return the symbol associated with ``event`` or ``None``."""

    analyze_phonetic(event)
    analyze_semantic(event)
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        cur = conn.execute(
            "SELECT symbol FROM event_symbol WHERE event = ?", (event,)
        )
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        if own_conn:
            conn.close()


# Ensure DB exists when module is imported
_ensure_db_file()


__all__ = [
    "get_connection",
    "set_event_symbol",
    "get_event_symbol",
    "DB_PATH",
    "SCHEMA_PATH",
]

