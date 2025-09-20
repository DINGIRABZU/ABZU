"""Deterministic stub of :mod:`chromadb` backed by text fixtures."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_BASELINE_PATH = Path(__file__).with_name("baseline.json")


def load_baseline_records(path: Path | None = None) -> list[dict[str, Any]]:
    """Return records stored in :mod:`baseline.json`."""

    target = path or _BASELINE_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    result: list[dict[str, Any]] = []
    for record in records:
        result.append(
            {
                "id": str(record["id"]),
                "embedding": [float(v) for v in record.get("embedding", [])],
                "metadata": dict(record.get("metadata", {})),
            }
        )
    return result


@dataclass
class _HistoryEntry:
    op: str
    data: dict[str, Any]


class FakeCollection:
    """In-memory substitute for a Chroma collection."""

    def __init__(self, records: Iterable[dict[str, Any]] | None = None) -> None:
        self.records: list[dict[str, Any]] = []
        self.history: list[_HistoryEntry] = []
        for record in records or ():
            self.records.append(
                {
                    "id": record["id"],
                    "embedding": [float(v) for v in record.get("embedding", [])],
                    "metadata": dict(record.get("metadata", {})),
                }
            )

    def add(  # type: ignore[override]
        self,
        ids: Any = None,
        embeddings: Any = None,
        metadatas: Any = None,
        **_: Any,
    ) -> None:
        """Store vectors in the collection.

        Supports both the legacy ``add(id, embedding, metadata)`` signature and
        the sequence form ``add(ids=[...], embeddings=[...], metadatas=[...])``.
        """

        if ids is None:
            ids_list: list[str] = []
        elif isinstance(ids, (list, tuple)):
            ids_list = [str(x) for x in ids]
        else:
            ids_list = [str(ids)]

        if embeddings is None:
            emb_list: list[list[float]] = []
        elif ids_list and not isinstance(embeddings, (list, tuple)):
            emb_list = [[float(x) for x in embeddings]]
        elif embeddings and isinstance(embeddings[0], (int, float)):
            emb_list = [[float(x) for x in embeddings]]
        else:
            emb_list = [[float(x) for x in emb] for emb in embeddings]

        if metadatas is None:
            meta_list: list[dict[str, Any]] = [{} for _ in ids_list]
        elif isinstance(metadatas, dict):
            meta_list = [dict(metadatas)]
        else:
            meta_list = [dict(meta) for meta in metadatas]

        self.history.append(
            _HistoryEntry(
                op="add",
                data={
                    "ids": list(ids_list),
                    "embeddings": [list(emb) for emb in emb_list],
                    "metadatas": [dict(meta) for meta in meta_list],
                },
            )
        )

        for rid, emb, meta in zip(ids_list, emb_list, meta_list):
            self.records.append({"id": rid, "embedding": emb, "metadata": meta})

    def query(  # type: ignore[override]
        self,
        query_embeddings: Any,
        n_results: int,
        **kwargs: Any,
    ) -> dict[str, list[list[Any]]]:
        """Return similarity-ordered matches."""

        if not query_embeddings:
            vectors: list[float] = []
        else:
            vectors = [float(x) for x in query_embeddings[0]]
        filters = kwargs.get("where") or kwargs.get("filter") or kwargs.get("filters")

        self.history.append(
            _HistoryEntry(
                op="query",
                data={
                    "query": list(vectors),
                    "n_results": n_results,
                    "filters": dict(filters) if isinstance(filters, dict) else None,
                },
            )
        )

        def _matches(meta: dict[str, Any]) -> bool:
            if not isinstance(filters, dict):
                return True
            for key, value in filters.items():
                if meta.get(key) != value:
                    return False
            return True

        def _similarity(vec: list[float]) -> float:
            if not vec or not vectors:
                return -1.0
            dot = sum(float(a) * float(b) for a, b in zip(vec, vectors))
            norm_vec = math.sqrt(sum(float(a) ** 2 for a in vec))
            norm_query = math.sqrt(sum(float(a) ** 2 for a in vectors))
            return float(dot / ((norm_vec * norm_query) + 1e-8))

        candidates = [rec for rec in self.records if _matches(rec["metadata"])]
        ordered = sorted(
            candidates,
            key=lambda rec: _similarity(rec["embedding"]),
            reverse=True,
        )[:n_results]

        return {
            "ids": [[rec["id"] for rec in ordered]],
            "embeddings": [[list(rec["embedding"]) for rec in ordered]],
            "metadatas": [[dict(rec["metadata"]) for rec in ordered]],
        }

    def snapshot(self, path: str | Path) -> None:
        target = Path(path)
        target.write_text(json.dumps(self.records), encoding="utf-8")


class FakePersistentClient:
    """Minimal persistent client that reuses :class:`FakeCollection`."""

    def __init__(
        self, path: str | Path, baseline: Iterable[dict[str, Any]] | None = None
    ) -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        baseline_records = [dict(record) for record in baseline or ()]
        self._baseline = [
            {
                "id": rec["id"],
                "embedding": list(rec.get("embedding", [])),
                "metadata": dict(rec.get("metadata", {})),
            }
            for rec in baseline_records
        ]
        self.collections: dict[str, FakeCollection] = {}

    def get_or_create_collection(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection(self._baseline)
        return self.collections[name]

    def create_collection(self, name: str) -> FakeCollection:
        collection = FakeCollection()
        self.collections[name] = collection
        return collection

    def delete_collection(self, name: str) -> None:
        self.collections.pop(name, None)

    def get_collection(self, name: str) -> FakeCollection:
        return self.collections[name]


class FakeChromaModule:
    """Namespace mimicking the public API of :mod:`chromadb`."""

    def __init__(self, baseline: Iterable[dict[str, Any]] | None = None) -> None:
        self._baseline = list(baseline or load_baseline_records())
        self.clients: dict[Path, FakePersistentClient] = {}

    def PersistentClient(
        self, path: str | Path
    ) -> FakePersistentClient:  # noqa: N802 - mimic chromadb
        key = Path(path)
        client = self.clients.get(key)
        if client is None:
            client = FakePersistentClient(key, baseline=self._baseline)
            self.clients[key] = client
        return client

    def get_collection(self, path: str | Path, name: str) -> FakeCollection:
        return self.clients[Path(path)].get_collection(name)


def stub_chromadb(
    monkeypatch: Any, module: Any, *, baseline: Iterable[dict[str, Any]] | None = None
) -> FakeChromaModule:
    """Patch ``module.chromadb`` with a :class:`FakeChromaModule` instance."""

    fake_module = FakeChromaModule(baseline=baseline)
    monkeypatch.setattr(module, "chromadb", fake_module)
    monkeypatch.setattr(module, "_HAVE_CHROMADB", True, raising=False)
    return fake_module


def materialize_sqlite(target_dir: str | Path) -> Path:
    """Write baseline records to a deterministic SQLite file.

    The schema is a lightweight surrogate for the real Chroma layout. Each
    row stores the JSON-encoded embedding and metadata for repeatable
    integration tests.
    """

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    db_path = target_dir / "fake_chroma.sqlite3"
    records = load_baseline_records()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                embedding TEXT,
                metadata TEXT
            )
            """
        )
        conn.execute("DELETE FROM records")
        for rec in records:
            conn.execute(
                "INSERT INTO records (id, embedding, metadata) VALUES (?, ?, ?)",
                (
                    rec["id"],
                    json.dumps(rec["embedding"]),
                    json.dumps(rec["metadata"]),
                ),
            )
        conn.commit()
    return db_path


__all__ = [
    "FakeChromaModule",
    "FakeCollection",
    "FakePersistentClient",
    "load_baseline_records",
    "materialize_sqlite",
    "stub_chromadb",
]
