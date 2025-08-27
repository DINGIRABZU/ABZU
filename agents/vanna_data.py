from __future__ import annotations

"""Vanna-powered data lookup agent.

Responsibilities:
- translate natural language prompts into SQL via vanna
- execute generated SQL queries
- store raw results in mental memory and narrative summaries in narrative memory
"""

from dataclasses import asdict
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from core.utils.optional_deps import lazy_import
from memory.mental import record_task_flow
from memory.narrative_engine import NarrativeEngine, StoryEvent
from agents import emit_event

vanna = lazy_import("vanna")
logger = logging.getLogger(__name__)


class _FileNarrativeEngine(NarrativeEngine):
    """Persist narrative events to ``data/narrative.log``."""

    def __init__(self, path: Path = Path("data/narrative.log")) -> None:
        self.path = path

    def record(self, event: StoryEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event)) + "\n")

    def stream(self) -> Iterable[StoryEvent]:
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                data = json.loads(line)
                yield StoryEvent(**data)


_narrative_engine = _FileNarrativeEngine()


def query_db(prompt: str) -> List[Dict[str, Any]]:
    """Query the configured database using a natural language ``prompt``.

    Returns a list of result rows as dictionaries. Requires the optional
    ``vanna`` dependency to be installed and configured with a database
    connection.
    """

    if getattr(vanna, "__stub__", False):  # pragma: no cover - optional dep
        raise RuntimeError("vanna library is not installed")

    emit_event("vanna_data", "task_delegated", {"prompt": prompt})
    sql, df, *_ = vanna.ask(prompt)  # type: ignore[attr-defined]
    rows = df.to_dict("records") if df is not None else []

    task_id = str(uuid4())
    context = {"prompt": prompt, "sql": sql, "rows": rows}
    try:
        record_task_flow(task_id, context)
    except Exception:  # pragma: no cover - best effort
        logger.debug("mental memory recording failed", exc_info=True)

    summary = f"{prompt} -> {len(rows)} rows"
    event = StoryEvent(actor="vanna_data", action=summary, symbolism=sql)
    try:
        _narrative_engine.record(event)
    except Exception:  # pragma: no cover - best effort
        logger.debug("narrative memory recording failed", exc_info=True)

    emit_event(
        "vanna_data",
        "task_completed",
        {"prompt": prompt, "rows": len(rows)},
    )

    return rows


__all__ = ["query_db"]
