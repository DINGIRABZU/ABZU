import types

import numpy as np

import memory_store as ms


def _patch_faiss(monkeypatch):
    class IndexFlatL2:
        def __init__(self, dim: int) -> None:
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

    dummy = types.SimpleNamespace(IndexFlatL2=IndexFlatL2)
    monkeypatch.setattr(ms, "faiss", dummy)
    monkeypatch.setattr(ms, "np", np)


def test_sharded_store_add_and_search(tmp_path, monkeypatch):
    _patch_faiss(monkeypatch)
    store = ms.ShardedMemoryStore(tmp_path / "base", shards=2)
    v1 = np.array([1.0, 0.0], dtype="float32")
    v2 = np.array([0.0, 1.0], dtype="float32")
    store.add("0", v1, {"n": "zero"})
    store.add("1", v2, {"n": "one"})
    assert set(store.ids) == {"0", "1"}
    ids1 = [r[0] for r in store.search(v1, 2)]
    ids2 = [r[0] for r in store.search(v2, 2)]
    assert "0" in ids1
    assert "1" in ids2


def test_sharded_store_snapshot_restore(tmp_path, monkeypatch):
    _patch_faiss(monkeypatch)
    base = tmp_path / "base"
    store = ms.ShardedMemoryStore(base, shards=2)
    vec = np.array([1.0, 0.0], dtype="float32")
    store.add("0", vec, {})
    snap = tmp_path / "snap"
    store.snapshot(snap)
    restored = ms.ShardedMemoryStore(tmp_path / "restored", shards=2)
    restored.restore(snap)
    assert restored.search(vec, 1)[0][0] == "0"
