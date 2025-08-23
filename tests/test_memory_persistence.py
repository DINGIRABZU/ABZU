"""Test concurrent vector memory persistence and recovery.

The test verifies that the vector memory store handles concurrent writes and
recovery after file deletion using a fake Redis backend.
"""

import threading
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

pytest.importorskip("faiss")
pytest.importorskip("redis")
pytest.importorskip("fakeredis")

import fakeredis

import vector_memory


def _embed(text: str) -> list[float]:
    return [float(ord(c) % 50) for c in text[:3]]


def test_concurrent_access_and_recovery():
    with TemporaryDirectory() as tmp:
        client = fakeredis.FakeRedis()
        vector_memory.configure(
            db_path=tmp,
            embedder=_embed,
            redis_client=client,
        )

        def worker(i: int) -> None:
            vector_memory.add_vector(f"text-{i}", {"i": i})

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(vector_memory.query_vectors(limit=100)) == 20

        db_file = Path(tmp) / "memory.sqlite"
        if db_file.exists():
            db_file.unlink()
        vector_memory._STORE = None  # reset
        vector_memory.configure(db_path=tmp, embedder=_embed, redis_client=client)

        assert len(vector_memory.query_vectors(limit=100)) == 20
