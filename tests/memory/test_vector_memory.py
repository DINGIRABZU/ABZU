"""Verify snapshot persistence and clustering for vector memory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import numpy as np
import vector_memory


def _embed(text: str) -> list[float]:
    """Deterministic embedder based on text length."""
    return [float(len(text))]


def _cluster_embed(text: str) -> np.ndarray:
    """Simple 2D embeddings to produce two distinct clusters."""
    if text.startswith("a"):
        return np.array([1.0, 0.0], dtype=float)
    return np.array([0.0, 1.0], dtype=float)


@pytest.fixture(autouse=True)
def reset_distance(monkeypatch) -> None:
    """Ensure distance cache is clear for each test."""
    monkeypatch.setattr(vector_memory, "_DIST", None)


def test_persist_and_restore_snapshot(tmp_path: Path) -> None:
    """Persist a snapshot and restore it from the latest file."""
    dbdir = tmp_path / "vm"
    vector_memory.configure(db_path=dbdir, embedder=_embed, snapshot_interval=1)
    vector_memory.add_vector("hello", {})

    snap_path = vector_memory.persist_snapshot()
    assert snap_path.exists()

    manifest = dbdir / "snapshots" / "manifest.json"
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert str(snap_path) in entries

    for f in dbdir.glob("*.sqlite"):
        f.unlink()

    vector_memory.configure(db_path=dbdir, embedder=_embed, snapshot_interval=1)
    assert vector_memory.restore_latest_snapshot() is True

    items = vector_memory.query_vectors(limit=10)
    assert any(i["text"] == "hello" for i in items)


def test_cluster_vectors_and_manifest(tmp_path: Path) -> None:
    """Cluster stored vectors and persist cluster manifest."""
    if getattr(vector_memory, "faiss", None) is None and getattr(
        vector_memory, "KMeans", None
    ) is None:
        pytest.skip("no clustering backend available")

    dbdir = tmp_path / "cluster"
    vector_memory.configure(db_path=dbdir, embedder=_cluster_embed, snapshot_interval=100)
    for t in ["a1", "a2", "b1", "b2"]:
        vector_memory.add_vector(t, {})

    clusters = vector_memory.cluster_vectors(k=2, limit=10)
    counts = sorted(c["count"] for c in clusters)
    assert counts == [2, 2]

    cluster_path = vector_memory.persist_clusters(k=2, limit=10)
    assert cluster_path.exists()
    manifest = dbdir / "snapshots" / "clusters_manifest.json"
    manifest_entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert str(cluster_path) in manifest_entries
