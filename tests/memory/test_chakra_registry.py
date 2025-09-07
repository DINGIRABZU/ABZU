from __future__ import annotations

import json
from pathlib import Path

from memory import chakra_registry as cr


class DummyVM:
    def __init__(self) -> None:
        self.path: Path | None = None
        self.data: list[dict[str, str]] = []

    def configure(self, db_path: str | Path | None = None, **_: object) -> None:
        if db_path is not None:
            self.path = Path(db_path)
            if self.path.exists():
                self.data = json.loads(self.path.read_text())
        elif self.path and self.path.exists():
            self.data = json.loads(self.path.read_text())

    def _save(self) -> None:
        if self.path is not None:
            self.path.write_text(json.dumps(self.data))

    def add_vector(self, text: str, meta: dict[str, str]) -> None:
        meta = dict(meta)
        meta.setdefault("text", text)
        self.data.append(meta)
        self._save()

    def search(
        self,
        query: str,
        filter: dict[str, str] | None = None,
        *,
        k: int = 5,
        scoring: str = "hybrid",
    ) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for item in self.data:
            if filter and any(item.get(k) != v for k, v in filter.items()):
                continue
            results.append(item)
        return results[:k]


def test_storage_retrieval_and_persistence(tmp_path, monkeypatch):
    dummy = DummyVM()
    monkeypatch.setattr(cr, "vector_memory", dummy)
    db = tmp_path / "mem.json"

    reg = cr.ChakraRegistry(db_path=db)
    reg.record("heart", "compassion", "unit-test")
    reg.record("root", "grounded", "unit-test")

    hits = reg.search("heart", "compassion")
    assert hits and hits[0]["chakra"] == "heart"
    assert all(h["chakra"] == "heart" for h in hits)

    reg2 = cr.ChakraRegistry(db_path=db)
    hits2 = reg2.search("heart", "compassion")
    assert hits2 and hits2[0]["source"] == "unit-test"
