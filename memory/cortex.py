from __future__ import annotations

"""Lightweight spiral memory stored as JSON lines.

The module maintains an inverted index for semantic ``tags`` and a companion
full‑text index allowing substring lookups. Read/write locks guard concurrent
access to the underlying files and queries may be executed in parallel via a
thread pool helper.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from threading import Condition, Lock
from typing import Any, Dict, Iterable, List, Protocol, Optional, Sequence, Set

from aspect_processor import analyze_phonetic, analyze_semantic, analyze_temporal


class SpiralNode(Protocol):
    """Protocol describing the minimal spiral node interface."""

    children: Iterable["SpiralNode"]

    def ask(self) -> None: ...

    def feel(self) -> None: ...

    def symbolize(self) -> None: ...

    def pause(self) -> None: ...

    def reflect(self) -> None: ...

    def decide(self) -> Dict[str, Any]: ...


CORTEX_MEMORY_FILE = Path("data/cortex_memory_spiral.jsonl")
# Inverted index mapping semantic tags to entry identifiers.
CORTEX_INDEX_FILE = Path("data/cortex_memory_index.json")


class _RWLock:
    """A minimal reader/writer lock."""

    def __init__(self) -> None:
        self._read_ready = Condition(Lock())
        self._readers = 0

    def acquire_read(self) -> None:
        with self._read_ready:
            self._readers += 1

    def release_read(self) -> None:
        with self._read_ready:
            self._readers -= 1
            if not self._readers:
                self._read_ready.notify_all()

    def acquire_write(self) -> None:
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self) -> None:
        self._read_ready.release()


_LOCK = _RWLock()


@contextmanager
def _read_locked() -> Iterable[None]:
    _LOCK.acquire_read()
    try:
        yield
    finally:
        _LOCK.release_read()


@contextmanager
def _write_locked() -> Iterable[None]:
    _LOCK.acquire_write()
    try:
        yield
    finally:
        _LOCK.release_write()


_TOKEN_RE = re.compile(r"[\w']+")


def _tokens(text: str) -> List[str]:
    """Return lowercase word tokens from ``text``."""
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _state_text(node: SpiralNode) -> str:
    """Return JSON string describing ``node`` state."""
    if is_dataclass(node):
        state = asdict(node)
    else:
        try:
            state = dict(node.__dict__)
        except Exception:
            state = {}
    return json.dumps(state, default=str)


def record_spiral(node: SpiralNode, decision: Dict[str, Any]) -> None:
    """Append ``node`` state and ``decision`` to :data:`CORTEX_MEMORY_FILE`.

    ``decision`` may include a ``tags`` list which is stored in an inverted
    index for fast lookup.
    """

    if not isinstance(decision, dict):
        raise ValueError("decision must be a dictionary")
    if node is None or not hasattr(node, "children"):
        raise ValueError("invalid spiral node")
    tags = decision.get("tags", [])
    if tags and (not isinstance(tags, list) or not all(isinstance(t, str) for t in tags)):
        raise ValueError("tags must be a list of strings")

    state = _state_text(node)
    analyze_phonetic(state)
    analyze_semantic(json.dumps(decision))
    analyze_temporal(datetime.utcnow().isoformat())

    with _write_locked():
        index: Dict[str, Any] = {}
        if CORTEX_INDEX_FILE.exists():
            index = json.loads(CORTEX_INDEX_FILE.read_text(encoding="utf-8"))
        entry_id = int(index.get("_next_id", 0))
        index["_next_id"] = entry_id + 1
        ft = index.setdefault("_fulltext", {})

        entry = {
            "id": entry_id,
            "timestamp": datetime.utcnow().isoformat(),
            "state": state,
            "decision": decision,
        }
        CORTEX_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CORTEX_MEMORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False))
            fh.write("\n")

        for tag in tags:
            index.setdefault(tag, []).append(entry_id)
            for tok in _tokens(tag):
                ft.setdefault(tok, []).append(entry_id)
        CORTEX_INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def query_spirals(
    filter: Optional[Dict[str, Any]] | None = None,
    tags: Optional[List[str]] = None,
    text: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return recorded spiral entries filtered by decision values or tags.

    ``tags`` performs exact tag matching while ``text`` does a full‑text search
    against tag tokens.
    """

    if filter is not None and not isinstance(filter, dict):
        raise ValueError("filter must be a dictionary or None")
    if tags and (not isinstance(tags, list) or not all(isinstance(t, str) for t in tags)):
        raise ValueError("tags must be a list of strings")
    if text is not None and not isinstance(text, str):
        raise ValueError("text must be a string or None")

    if not CORTEX_MEMORY_FILE.exists():
        return []

    ids: Optional[Set[int]] = None
    with _read_locked():
        index: Dict[str, Any] = {}
        if (tags or text) and CORTEX_INDEX_FILE.exists():
            index = json.loads(CORTEX_INDEX_FILE.read_text(encoding="utf-8"))
        if tags:
            for tag in tags:
                tag_ids = set(index.get(tag, []))
                ids = tag_ids if ids is None else ids & tag_ids
            if ids is None:
                ids = set()
        if text:
            ft_index = index.get("_fulltext", {})
            txt_ids: Optional[Set[int]] = None
            for tok in _tokens(text):
                tok_ids = set(ft_index.get(tok, []))
                txt_ids = tok_ids if txt_ids is None else txt_ids & tok_ids
            if txt_ids is None:
                txt_ids = set()
            ids = txt_ids if ids is None else ids & txt_ids

        entries: List[Dict[str, Any]] = []
        with CORTEX_MEMORY_FILE.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                entry_id = int(data.get("id", -1))
                if ids is not None and entry_id not in ids:
                    continue
                if filter:
                    dec = data.get("decision", {})
                    for key, val in filter.items():
                        if dec.get(key) != val:
                            break
                    else:
                        entries.append(data)
                    continue
                entries.append(data)
    return entries


def query_spirals_concurrent(requests: Sequence[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Execute multiple :func:`query_spirals` calls concurrently.

    Each mapping in ``requests`` is passed as keyword arguments to
    :func:`query_spirals`. The function returns a list of results in the same
    order.
    """

    with ThreadPoolExecutor() as exe:
        futures = [exe.submit(query_spirals, **req) for req in requests]
        return [f.result() for f in futures]


def prune_spirals(keep: int) -> None:
    """Keep only the newest ``keep`` entries in memory."""

    if keep < 0:
        raise ValueError("keep must be non-negative")
    if not CORTEX_MEMORY_FILE.exists():
        return

    with _write_locked():
        lines = CORTEX_MEMORY_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) <= keep:
            return
        keep_lines = lines[:keep]
        CORTEX_MEMORY_FILE.write_text("\n".join(keep_lines) + "\n", encoding="utf-8")

        # rebuild index
        index: Dict[str, Any] = {"_next_id": len(keep_lines), "_fulltext": {}}
        ft = index["_fulltext"]
        for i, line in enumerate(keep_lines):
            try:
                data = json.loads(line)
            except Exception:
                continue
            for tag in data.get("decision", {}).get("tags", []):
                if isinstance(tag, str):
                    index.setdefault(tag, []).append(i)
                    for tok in _tokens(tag):
                        ft.setdefault(tok, []).append(i)
        CORTEX_INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def export_spirals(
    path: Path,
    tags: Optional[List[str]] = None,
    filter: Optional[Dict[str, Any]] = None,
    text: Optional[str] = None,
) -> None:
    """Export spiral entries matching ``tags``/``text`` and ``filter`` to ``path``."""

    path = Path(path)
    entries = query_spirals(filter=filter, tags=tags, text=text)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "record_spiral",
    "query_spirals",
    "query_spirals_concurrent",
    "prune_spirals",
    "export_spirals",
    "CORTEX_MEMORY_FILE",
    "CORTEX_INDEX_FILE",
    "SpiralNode",
]
