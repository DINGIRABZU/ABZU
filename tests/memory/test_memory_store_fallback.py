"""Tests for memory store fallback."""

import memory_store as ms


def test_add_search_and_delete_without_optional_dependencies(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "faiss", None)
    monkeypatch.setattr(ms, "np", None)
    db = tmp_path / "store.sqlite"
    store = ms.MemoryStore(db)
    store.add("a", [1.0, 0.0], {"n": "a"})
    store.add("b", [0.0, 1.0], {"n": "b"})
    ids = [r[0] for r in store.search([1.0, 0.0], 2)]
    assert "a" in ids and "b" in ids
    store.delete(["a"])
    ids_after = [r[0] for r in store.search([1.0, 0.0], 2)]
    assert "a" not in ids_after
