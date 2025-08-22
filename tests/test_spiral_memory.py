from __future__ import annotations

from pathlib import Path

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
