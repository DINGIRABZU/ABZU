"""Exercise FAISS/SQLite backed vector persistence.

The test verifies that vectors written to a temporary :class:`~memory_store.MemoryStore`
can be searched after instantiation and removed from the backend.  Runtime is
expected to be well below one second on modest hardware.
"""

from __future__ import annotations

import pytest

pytest.importorskip("faiss")
pytest.importorskip("numpy")

import numpy as np

from memory_store import MemoryStore


def test_insert_search_delete(tmp_path):
    """Insert, retrieve and delete a vector in a temporary store."""
    db = tmp_path / "store.sqlite"
    store = MemoryStore(db)

    vec = np.array([1.0, 0.0], dtype="float32")
    store.add("a", vec, {"value": 1})

    # search should find the inserted vector
    res = store.search(vec, 1)
    assert res and res[0][0] == "a"
    assert res[0][2]["value"] == 1

    # ensure persistence across instances
    store2 = MemoryStore(db)
    res2 = store2.search(vec, 1)
    assert res2 and res2[0][0] == "a"

    # delete from SQLite and reload
    with store2._connection() as conn:  # type: ignore[attr-defined]
        conn.execute("DELETE FROM memory WHERE id=?", ("a",))
        conn.commit()
    store2._load()  # type: ignore[attr-defined]

    assert store2.search(vec, 1) == []
