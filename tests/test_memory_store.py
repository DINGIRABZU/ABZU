"""Tests for memory store."""

from __future__ import annotations

import types

import numpy as np

import memory_store as ms


def _patch_faiss(monkeypatch):
    """Provide a minimal FAISS substitute for testing."""

    class IndexFlatL2:
        def __init__(self, dim: int):
            self.vectors: list[np.ndarray] = []

        def add(self, arr: np.ndarray) -> None:
            for row in arr:
                self.vectors.append(np.asarray(row, dtype="float32"))

        def search(self, vec: np.ndarray, k: int):
            if not self.vectors:
                return np.empty((1, k)), np.full((1, k), -1)
            arr = np.stack(self.vectors)
            dists = np.sum((arr - vec) ** 2, axis=1)
            idxs = np.argsort(dists)[:k]
            return dists[idxs][None, :], idxs[None, :]

        def reconstruct(self, idx: int) -> np.ndarray:
            return self.vectors[idx]

    dummy_faiss = types.SimpleNamespace(IndexFlatL2=IndexFlatL2)
    monkeypatch.setattr(ms, "faiss", dummy_faiss)
    monkeypatch.setattr(ms, "np", np)


def test_memory_store_roundtrip(tmp_path, monkeypatch):
    _patch_faiss(monkeypatch)
    db = tmp_path / "store.sqlite"
    store = ms.MemoryStore(db)
    vec = np.array([1.0, 0.0], dtype="float32")
    store.add("a", vec, {"foo": "bar"})
    res = store.search(vec, 1)
    assert res and res[0][0] == "a"
    assert res[0][2]["foo"] == "bar"

    # rewrite vector and metadata
    new_vec = np.array([0.0, 1.0], dtype="float32")
    store.rewrite("a", new_vec, {"foo": "baz"})
    res2 = store.search(new_vec, 1)
    assert res2 and res2[0][0] == "a"
    assert res2[0][2]["foo"] == "baz"

    snap = tmp_path / "snap.sqlite"
    store.snapshot(snap)
    store.restore(snap)
    res3 = store.search(new_vec, 1)
    assert res3 and res3[0][2]["foo"] == "baz"


def test_auto_snapshot(tmp_path, monkeypatch):
    _patch_faiss(monkeypatch)
    db = tmp_path / "store.sqlite"
    store = ms.MemoryStore(db, snapshot_interval=1)
    vec = np.array([1.0, 0.0], dtype="float32")
    store.add("a", vec, {})
    snap_dir = db.parent / "snapshots"
    assert snap_dir.exists() and any(snap_dir.iterdir())
