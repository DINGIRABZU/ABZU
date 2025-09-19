"""Tests for spiral memory."""

from __future__ import annotations

import sqlite3
import types
from typing import Any

import pytest

import spiral_memory as spiral_memory_module
from spiral_memory import SpiralMemory, spiral_recall


def test_spiral_memory_register_and_recall(tmp_path, monkeypatch):
    monkeypatch.setattr("spiral_memory.torch", None)
    monkeypatch.setattr("spiral_memory.nn", None)
    db_file = tmp_path / "spiral.db"
    memory = SpiralMemory(db_path=db_file)
    monkeypatch.setattr("spiral_memory.DEFAULT_MEMORY", memory)

    memory.add_layer([1.0, 2.0])
    memory.add_layer([3.0, 4.0])
    assert memory.aggregate() == [2.0, 3.0]

    memory.register_event("alpha")
    memory.register_event("beta")

    result = spiral_recall("query")
    assert "alpha" in result and "beta" in result
    assert db_file.exists()


def test_optional_spiral_memory_recall(monkeypatch, tmp_path):
    optional_sm = pytest.importorskip("memory.optional.spiral_memory")

    memory = optional_sm.SpiralMemory(db_path=tmp_path / "optional.db", width=8)
    # The optional implementation is a full no-op – adding layers or
    # registering events should not raise nor persist anything.
    memory.add_layer([0.1, 0.2, 0.3])
    memory.register_event("noop", layers={"layer": [0.1]})

    assert memory.aggregate() == []
    assert memory.recall("anything") == ""

    # Verify the module-level helper routes through the default memory
    # instance even after monkeypatching.
    monkeypatch.setattr(optional_sm, "DEFAULT_MEMORY", memory)
    assert optional_sm.spiral_recall("question") == ""


def test_register_event_handles_glyph_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("spiral_memory.torch", None)
    monkeypatch.setattr("spiral_memory.nn", None)
    db_file = tmp_path / "spiral_fail.db"
    memory = SpiralMemory(db_path=db_file)

    def _raise(_: dict) -> tuple[str, str]:
        raise RuntimeError("boom")

    monkeypatch.setattr("spiral_memory.generate_sacred_glyph", _raise)
    memory.register_event("gamma", layers={"root": [0.1]})

    with sqlite3.connect(db_file) as conn:
        rows = conn.execute(
            "SELECT event, glyph_path, phrase FROM events ORDER BY id DESC LIMIT 1"
        ).fetchall()
    assert rows[0] == ("gamma", None, None)


def test_register_event_records_glyph(tmp_path, monkeypatch):
    monkeypatch.setattr("spiral_memory.torch", None)
    monkeypatch.setattr("spiral_memory.nn", None)
    db_file = tmp_path / "spiral_success.db"
    memory = SpiralMemory(db_path=db_file)
    glyph_path = tmp_path / "glyph.png"

    def _generate(_: dict) -> tuple[str, str]:
        glyph_path.write_text("g")
        return str(glyph_path), "sigil"

    monkeypatch.setattr("spiral_memory.generate_sacred_glyph", _generate)
    memory.register_event("delta", layers={"root": [0.2]})

    with sqlite3.connect(db_file) as conn:
        row = conn.execute(
            "SELECT event, glyph_path, phrase FROM events ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row == ("delta", str(glyph_path), "sigil")


def test_connect_adds_missing_columns(tmp_path):
    db_file = tmp_path / "columns.db"
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            "CREATE TABLE events (id INTEGER PRIMARY KEY, timestamp TEXT, event TEXT)"
        )
    conn = spiral_memory_module._connect(db_file)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
    assert {"glyph_path", "phrase"} <= cols


def test_recall_with_torch_stub(monkeypatch, tmp_path):
    class DummyTensor:
        def __init__(self, data):
            if isinstance(data, DummyTensor):
                data = data.tolist()
            self._data = data

        def mean(self, dim=0):
            data = self.tolist()
            if not data:
                return DummyTensor([])

            if isinstance(data, DummyTensor):
                data = data.tolist()

            if isinstance(data, (list, tuple)):
                rows: list[list[Any]] = []
                for row in data:
                    if isinstance(row, DummyTensor):
                        row = row.tolist()
                    if not isinstance(row, (list, tuple)):
                        row = [row]
                    rows.append(list(row))
            else:
                rows = [[data]]

            agg = [sum(col) / len(col) for col in zip(*rows)]
            return DummyTensor(agg)

        def tolist(self):
            data = self._data
            if isinstance(data, DummyTensor):
                return data.tolist()
            if isinstance(data, (list, tuple)):
                return [
                    item.tolist() if isinstance(item, DummyTensor) else item
                    for item in data
                ]
            return data

    stub_torch = types.SimpleNamespace(
        tensor=lambda data, dtype=None: DummyTensor(data), float32=float
    )
    monkeypatch.setattr(spiral_memory_module, "torch", stub_torch)

    class DummyModel:
        def __call__(self, data):
            return DummyTensor(data)

    def _fake_post_init(self):
        self._model = DummyModel()

    monkeypatch.setattr(
        spiral_memory_module.SpiralMemory,
        "__post_init__",
        _fake_post_init,
        raising=False,
    )

    memory = SpiralMemory(db_path=tmp_path / "torch.db")
    memory.add_layer([1.0, 3.0])
    memory.add_layer([3.0, 5.0])
    glyph_path = tmp_path / "glyph.png"
    monkeypatch.setattr(
        spiral_memory_module,
        "generate_sacred_glyph",
        lambda layers: (str(glyph_path), "sigil"),
    )
    memory.register_event("event", layers={"root": [0.1]})

    result = memory.recall("ask")
    assert "event ({} | sigil)".format(str(glyph_path)) in result
    assert "signal" in result
