"""Tests for the spiritual memory ontology database."""

from memory_spiritual import (
    get_connection,
    map_to_symbol,
    get_event_symbol,
    lookup_symbol_history,
)


def test_connection_initializes_schema():
    """An in-memory connection creates the schema automatically."""

    conn = get_connection(":memory:")
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='event_symbol'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_event_symbol_roundtrip():
    """Storing and retrieving a symbol works with in-memory DB."""

    conn = get_connection(":memory:")
    map_to_symbol(("rain", "☔"), conn=conn)
    assert get_event_symbol("rain", conn=conn) == "☔"
    assert lookup_symbol_history("☔", conn=conn) == ["rain"]
    conn.close()

