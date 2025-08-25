"""Integration tests for extended vector memory features."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

import vector_memory
from src.core.utils.seed import seed_all


seed_all(123)


def _embed(_: str) -> np.ndarray:
    return np.array([1.0, 0.0], dtype=float)


def test_persistence_with_snapshot(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vector_memory, "_DIST", None)
    dbdir = tmp_path / "db"
    vector_memory.configure(
        db_path=dbdir, embedder=_embed, shards=2, snapshot_interval=1
    )
    vector_memory.add_vectors(["one", "two"], [{}, {}])
    snap = tmp_path / "snapshot"
    vector_memory.snapshot(snap)

    vector_memory.configure(db_path=tmp_path / "db2", embedder=_embed, shards=2)
    vector_memory.restore(snap)
    items = vector_memory.query_vectors(limit=10)
    texts = {i["text"] for i in items}
    assert {"one", "two"} <= texts


def test_decay_weighting(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vector_memory, "_DIST", None)
    dbdir = tmp_path / "decay"
    vector_memory.configure(
        db_path=dbdir,
        embedder=_embed,
        decay_strategy="exponential",
        decay_seconds=1.0,
    )
    now = datetime.utcnow()
    vector_memory.add_vector("recent", {"timestamp": now.isoformat()})
    vector_memory.add_vector(
        "old", {"timestamp": (now - timedelta(seconds=10)).isoformat()}
    )
    res = vector_memory.search("query", k=2)
    assert [r["text"] for r in res] == ["recent", "old"]


def test_distributed_backup(monkeypatch, tmp_path: Path) -> None:
    class DummyDist:
        def __init__(self) -> None:
            self.records: dict[str, tuple[list[float], dict]] = {}

        def backup(self, id_, emb, meta) -> None:  # type: ignore[no-untyped-def]
            self.records[id_] = (emb, meta)

        def restore_to(self, store) -> None:  # type: ignore[no-untyped-def]
            for id_, (emb, meta) in self.records.items():
                store.add(id_, emb, meta)

    dist = DummyDist()
    monkeypatch.setattr(vector_memory, "_DIST", dist)
    vector_memory.configure(db_path=tmp_path / "dist", embedder=_embed)
    vector_memory.add_vector("hello", {})
    assert dist.records

    vector_memory.configure(db_path=tmp_path / "dist2", embedder=_embed)
    res = vector_memory.search("hello", k=1)
    assert res and res[0]["text"] == "hello"


def test_background_compaction(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(vector_memory, "_DIST", None)
    dbdir = tmp_path / "comp"
    vector_memory.configure(
        db_path=dbdir,
        embedder=_embed,
        decay_strategy="exponential",
        decay_seconds=0.1,
        compaction_interval=0.2,
        decay_threshold=0.5,
    )
    vector_memory.add_vector(
        "stale",
        {"timestamp": (datetime.utcnow() - timedelta(seconds=10)).isoformat()},
    )
    time.sleep(0.5)
    items = vector_memory.query_vectors(limit=10)
    texts = [i["text"] for i in items]
    assert "stale" not in texts
