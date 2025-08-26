"""Concurrency checks for cortex memory operations.

The tests ensure parallel writes maintain a consistent index and that the file
lock used in :mod:`memory.cortex` is properly created and released.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import fcntl

from memory import cortex as cortex_memory


class DummyNode:
    """Minimal spiral node for recording."""

    def __init__(self, val: str) -> None:
        self.val = val
        self.children = []

    def ask(self) -> None: ...  # pragma: no cover
    def feel(self) -> None: ...  # pragma: no cover
    def symbolize(self) -> None: ...  # pragma: no cover
    def pause(self) -> None: ...  # pragma: no cover
    def reflect(self) -> None: ...  # pragma: no cover
    def decide(self) -> dict[str, str]:  # pragma: no cover
        return {"action": self.val}


def test_parallel_record_spiral_index(tmp_path, monkeypatch) -> None:
    """Multiple writers update the index without losing entries."""

    log_file = tmp_path / "spiral.jsonl"
    index_file = tmp_path / "index.json"
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)
    monkeypatch.setattr(cortex_memory, "CORTEX_INDEX_FILE", index_file)

    node = DummyNode("N")

    def writer(i: int) -> None:
        cortex_memory.record_spiral(node, {"tags": [f"tag{i}"]})

    with ThreadPoolExecutor(max_workers=5) as ex:
        for i in range(20):
            ex.submit(writer, i)

    ids = set()
    for i in range(20):
        res = cortex_memory.search_index(tags=[f"tag{i}"])
        assert len(res) == 1
        ids.update(res)

    assert ids == set(range(20))


def test_lock_file_created_and_released(tmp_path, monkeypatch) -> None:
    """record_spiral creates a lock file and releases the lock."""

    log_file = tmp_path / "spiral.jsonl"
    index_file = tmp_path / "index.json"
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)
    monkeypatch.setattr(cortex_memory, "CORTEX_INDEX_FILE", index_file)

    node = DummyNode("L")
    cortex_memory.record_spiral(node, {"tags": ["one"]})

    lock_path = index_file.with_suffix(".lock")
    assert lock_path.exists()

    with open(lock_path, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(lf, fcntl.LOCK_UN)
