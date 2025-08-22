"""Tests for the spiritual memory ontology database."""

from __future__ import annotations

from memory import spiritual as ms


def test_connection_initializes_schema():
    """An in-memory connection creates the schema automatically."""

    conn = ms.get_connection(":memory:")
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='event_symbol'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_event_symbol_roundtrip():
    """Storing and retrieving a symbol works with in-memory DB."""

    conn = get_connection(":memory:")
    ms.map_to_symbol(("rain", "☔"), conn=conn)
    assert ms.get_event_symbol("rain", conn=conn) == "☔"
    assert ms.lookup_symbol_history("☔", conn=conn) == ["rain"]
    conn.close()
