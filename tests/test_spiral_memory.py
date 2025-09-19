"""Tests for spiral memory."""

from __future__ import annotations

import pytest

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
