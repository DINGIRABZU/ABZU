from __future__ import annotations

"""Store retrieval insights for the spiral cortex."""

from datetime import datetime
from pathlib import Path
import json
from typing import Any, Iterable, List


INSIGHT_FILE = Path("data/spiral_cortex_memory.jsonl")


def log_insight(question: str, snippets: Iterable[dict[str, Any]], sentiment: float) -> None:
    """Append ``question`` and ``snippets`` to :data:`INSIGHT_FILE`."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "snippets": list(snippets),
        "sentiment": sentiment,
    }
    INSIGHT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INSIGHT_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")


def load_insights(limit: int | None = None) -> List[dict[str, Any]]:
    """Return logged insights ordered from oldest to newest."""
    if not INSIGHT_FILE.exists():
        return []
    entries: List[dict[str, Any]] = []
    with INSIGHT_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
    if limit is not None:
        entries = entries[-limit:]
    return entries


__all__ = ["log_insight", "load_insights", "INSIGHT_FILE"]
