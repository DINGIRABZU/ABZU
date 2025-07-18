from __future__ import annotations

"""Lightweight spiral memory stored as JSON lines."""

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict, Iterable, Protocol, List


class SpiralNode(Protocol):
    """Protocol describing the minimal spiral node interface."""

    children: Iterable["SpiralNode"]

    def ask(self) -> None:
        ...

    def feel(self) -> None:
        ...

    def symbolize(self) -> None:
        ...

    def pause(self) -> None:
        ...

    def reflect(self) -> None:
        ...

    def decide(self) -> Dict[str, Any]:
        ...


CORTEX_MEMORY_FILE = Path("data/cortex_memory_spiral.jsonl")


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
    """Append ``node`` state and ``decision`` to :data:`CORTEX_MEMORY_FILE`."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "state": _state_text(node),
        "decision": decision,
    }
    CORTEX_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CORTEX_MEMORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")


def query_spirals(filter: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Return recorded spiral entries optionally filtered by decision values."""
    if not CORTEX_MEMORY_FILE.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with CORTEX_MEMORY_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                data = json.loads(line)
            except Exception:
                continue
            if filter:
                skip = False
                dec = data.get("decision", {})
                for key, val in filter.items():
                    if dec.get(key) != val:
                        skip = True
                        break
                if skip:
                    continue
            entries.append(data)
    return entries


__all__ = ["record_spiral", "query_spirals", "CORTEX_MEMORY_FILE", "SpiralNode"]
