# pydocstyle: skip-file
"""SQLite-backed event ↔ symbol memory.

On import the module ensures ``data/ontology.db`` exists, creating it from
``data/ontology_schema.sql`` if necessary. This keeps the ontology database
out of version control while providing a lightweight persistent mapping.

Legacy helpers :func:`set_event_symbol` and :func:`get_event_symbol` are kept
for backward compatibility. The specification-aligned names are
``map_to_symbol`` for storing mappings and ``lookup_symbol_history`` for
querying the reverse direction.
"""

from __future__ import annotations

__version__ = "0.1.1"

import sqlite3
from pathlib import Path
from typing import Optional

from aspect_processor import analyze_phonetic, analyze_ritual, analyze_semantic

BASE_DIR = Path(__file__).resolve().parents[1]
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
    """Legacy name for storing the symbol associated with ``event``.

    The specification refers to this operation as :func:`map_to_symbol`.
    """

    analyze_phonetic(event)
    analyze_semantic(symbol)
    analyze_ritual(f"{event}:{symbol}")
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


def map_to_symbol(
    event_metadata: tuple[str, str] | dict[str, str],
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """Spec-aligned wrapper around :func:`set_event_symbol`.

    Parameters
    ----------
    event_metadata:
        Either a ``(event, symbol)`` tuple or a mapping with ``"event"`` and
        ``"symbol"`` keys.
    conn:
        Optional SQLite connection to use.
    """

    if isinstance(event_metadata, dict):
        event = event_metadata["event"]
        symbol = event_metadata["symbol"]
    else:
        event, symbol = event_metadata
    set_event_symbol(event, symbol, conn=conn)


def get_event_symbol(
    event: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[str]:
    """Legacy lookup returning the symbol associated with ``event``.

    This direction is retained for backward compatibility; the specification
    adds :func:`lookup_symbol_history` for reverse queries.
    """

    analyze_phonetic(event)
    analyze_semantic(event)
    analyze_ritual(event)
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        cur = conn.execute("SELECT symbol FROM event_symbol WHERE event = ?", (event,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        if own_conn:
            conn.close()


def lookup_symbol_history(
    symbol: str, conn: Optional[sqlite3.Connection] = None
) -> list[str]:
    """Return all events previously mapped to ``symbol``.

    This is the specification-aligned inverse of :func:`get_event_symbol`.
    """

    analyze_phonetic(symbol)
    analyze_semantic(symbol)
    analyze_ritual(symbol)
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        cur = conn.execute("SELECT event FROM event_symbol WHERE symbol = ?", (symbol,))
        return [row[0] for row in cur.fetchall()]
    finally:
        if own_conn:
            conn.close()


# Ensure DB exists when module is imported
_ensure_db_file()


__all__ = [
    "get_connection",
    "set_event_symbol",
    "map_to_symbol",
    "get_event_symbol",
    "lookup_symbol_history",
    "DB_PATH",
    "SCHEMA_PATH",
]
