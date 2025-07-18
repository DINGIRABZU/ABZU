from __future__ import annotations

"""Append and read JSONL interaction records for corpus memory usage."""

from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Any, List

INTERACTIONS_FILE = Path("data/interactions.jsonl")
logger = logging.getLogger(__name__)


def log_interaction(
    input_text: str,
    intent: dict,
    result: dict,
    outcome: str,
    *,
    source_type: str | None = None,
    genre: str | None = None,
    instrument: str | None = None,
) -> None:
    """Append ``input_text`` and ``result`` details to :data:`INTERACTIONS_FILE`.

    Additional metadata can be provided via ``source_type`` , ``genre`` and
    ``instrument`` which will be stored alongside the interaction.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": input_text,
        "intent": intent,
        "result": result,
        "outcome": outcome,
    }
    emotion = result.get("emotion") or intent.get("emotion")
    if emotion is not None:
        entry["emotion"] = emotion
    if source_type is not None:
        entry["source_type"] = source_type
    if genre is not None:
        entry["genre"] = genre
    if instrument is not None:
        entry["instrument"] = instrument
    INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INTERACTIONS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")
    logger.info("logged interaction to %s", INTERACTIONS_FILE)


def load_interactions(limit: int | None = None) -> List[dict[str, Any]]:
    """Return recorded interactions ordered from oldest to newest."""
    if not INTERACTIONS_FILE.exists():
        return []
    entries: List[dict[str, Any]] = []
    with INTERACTIONS_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                entries.append(json.loads(line))
            except Exception as exc:
                logger.error("invalid json line in %s: %s", INTERACTIONS_FILE, exc)
                continue
    if limit is not None:
        entries = entries[-limit:]
    return entries


def log_ritual_result(name: str, steps: List[str]) -> None:
    """Append a ritual invocation entry to :data:`INTERACTIONS_FILE`."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "ritual": name,
        "steps": steps,
    }
    INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INTERACTIONS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")
    logger.info("logged ritual %s to %s", name, INTERACTIONS_FILE)


__all__ = [
    "log_interaction",
    "load_interactions",
    "log_ritual_result",
    "INTERACTIONS_FILE",
]
