"""Tests for the spiritual memory ontology database."""

from __future__ import annotations

from memory import spiritual as ms


def _silence_analyzers(monkeypatch) -> None:
    """Replace heavy analyzers with no-op stubs."""

    for name in ("analyze_phonetic", "analyze_semantic", "analyze_ritual"):
        monkeypatch.setattr(ms, name, lambda *a, **kw: None)


def test_connection_initializes_schema(monkeypatch):
    """An in-memory connection creates the schema automatically."""

    _silence_analyzers(monkeypatch)
    conn = ms.get_connection(":memory:")
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='event_symbol'",
    )
    assert cur.fetchone() is not None
    conn.close()


def test_event_symbol_roundtrip(monkeypatch):
    """Storing and retrieving symbols works with tuples and dicts."""

    _silence_analyzers(monkeypatch)
    conn = ms.get_connection(":memory:")
    ms.map_to_symbol(("rain", "☔"), conn=conn)
    ms.map_to_symbol({"event": "sun", "symbol": "☀"}, conn=conn)
    assert ms.get_event_symbol("rain", conn=conn) == "☔"
    assert ms.lookup_symbol_history("☀", conn=conn) == ["sun"]
    assert ms.get_event_symbol("moon", conn=conn) is None
    assert ms.lookup_symbol_history("☽", conn=conn) == []
    conn.close()
