from __future__ import annotations

import numpy as np

from memory_store import MemoryStore


def test_memory_store_roundtrip(tmp_path):
    db = tmp_path / "store.sqlite"
    store = MemoryStore(db)
    vec = np.array([1.0, 0.0], dtype="float32")
    store.add("a", vec, {"foo": "bar"})
    res = store.search(vec, 1)
    assert res and res[0][2]["foo"] == "bar"
    snap = tmp_path / "snap.sqlite"
    store.snapshot(snap)
    store.restore(snap)
    res = store.search(vec, 1)
    assert res and res[0][2]["foo"] == "bar"
