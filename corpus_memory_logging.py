from __future__ import annotations

"""Append and read JSONL interaction records for corpus memory usage."""

import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, List

INTERACTIONS_FILE = Path("data/interactions.jsonl")
MAX_BYTES = int(os.getenv("CORPUS_LOG_MAX_BYTES", 1_048_576))
BACKUP_COUNT = int(os.getenv("CORPUS_LOG_BACKUP_COUNT", 5))
logger = logging.getLogger(__name__)
file_logger = logging.getLogger(__name__ + ".file")
file_logger.propagate = False
file_logger.setLevel(logging.INFO)


def _ensure_file_logger() -> logging.Logger:
    """Configure and return the rotating file logger."""
    if file_logger.handlers:
        handler = file_logger.handlers[0]
        needs_update = (
            getattr(handler, "baseFilename", "") != str(INTERACTIONS_FILE)
            or getattr(handler, "maxBytes", None) != MAX_BYTES
            or getattr(handler, "backupCount", None) != BACKUP_COUNT
        )
        if not needs_update:
            return file_logger
        file_logger.removeHandler(handler)
        handler.close()
    INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        INTERACTIONS_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    file_logger.addHandler(handler)
    return file_logger


def log_interaction(
    input_text: str,
    intent: dict,
    result: dict,
    outcome: str,
    *,
    source_type: str | None = None,
    genre: str | None = None,
    instrument: str | None = None,
    feedback: str | None = None,
    rating: float | None = None,
) -> None:
    """Append ``input_text`` and ``result`` details to :data:`INTERACTIONS_FILE`.

    Additional metadata can be provided via ``source_type`` , ``genre`` and
    ``instrument`` which will be stored alongside the interaction. Optional
    ``feedback`` text and numeric ``rating`` values are also persisted when
    supplied.
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
    if feedback is not None:
        entry["feedback"] = feedback
    if rating is not None:
        entry["rating"] = rating
    _ensure_file_logger().info(json.dumps(entry, ensure_ascii=False))
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
    _ensure_file_logger().info(json.dumps(entry, ensure_ascii=False))
    logger.info("logged ritual %s to %s", name, INTERACTIONS_FILE)


__all__ = [
    "log_interaction",
    "load_interactions",
    "log_ritual_result",
    "INTERACTIONS_FILE",
]
