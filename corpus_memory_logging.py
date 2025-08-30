"""Append and read JSONL interaction records for corpus memory usage."""

from __future__ import annotations

__version__ = "0.0.0"

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

INTERACTIONS_FILE = Path("data/interactions.jsonl")
"""Primary JSONL log file for interaction records."""

QUARANTINE_FILE = INTERACTIONS_FILE.with_suffix(".quarantine.jsonl")
"""Location for quarantined malformed records."""

MAX_LOG_SIZE = 1_000_000
"""Maximum size in bytes before the log file is rotated."""

logger = logging.getLogger(__name__)


def _rotate_if_needed() -> None:
    """Rotate the interactions log when it grows beyond ``MAX_LOG_SIZE``."""

    if INTERACTIONS_FILE.exists() and INTERACTIONS_FILE.stat().st_size >= MAX_LOG_SIZE:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rotated = INTERACTIONS_FILE.with_name(
            f"{INTERACTIONS_FILE.stem}-{ts}{INTERACTIONS_FILE.suffix}"
        )
        INTERACTIONS_FILE.rename(rotated)
        logger.info("rotated interaction log to %s", rotated)


def watchdog() -> None:
    """Quarantine malformed JSONL entries and keep the log clean."""

    if not INTERACTIONS_FILE.exists():
        return

    valid: list[str] = []
    bad: list[str] = []
    with INTERACTIONS_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                json.loads(line)
                valid.append(line)
            except Exception:
                bad.append(line)

    if bad:
        QUARANTINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with QUARANTINE_FILE.open("a", encoding="utf-8") as qh:
            qh.writelines(bad)
        with INTERACTIONS_FILE.open("w", encoding="utf-8") as fh:
            fh.writelines(valid)
        logger.error(
            "quarantined %d malformed entries",
            len(bad),
            extra={"event": "corpus_watchdog"},
        )


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

    INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed()
    with INTERACTIONS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")
    logger.info("logged interaction to %s", INTERACTIONS_FILE)


def log_suggestion(text: str, context: Dict[str, Any] | None = None) -> None:
    """Append a plain suggestion entry to :data:`INTERACTIONS_FILE`.

    ``context`` can include auxiliary metadata such as failure counts.  Entries are
    stored with a ``suggestion`` field to differentiate them from full
    interactions.
    """

    entry: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "suggestion": text,
    }
    if context:
        entry["context"] = context

    INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed()
    with INTERACTIONS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")
    logger.info("logged suggestion to %s", INTERACTIONS_FILE)


def load_interactions(limit: int | None = None) -> List[dict[str, Any]]:
    """Return recorded interactions ordered from oldest to newest."""

    watchdog()
    if not INTERACTIONS_FILE.exists():
        return []

    entries: List[dict[str, Any]] = []
    with INTERACTIONS_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            entries.append(json.loads(line))
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
    _rotate_if_needed()
    with INTERACTIONS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False))
        fh.write("\n")
    logger.info("logged ritual %s to %s", name, INTERACTIONS_FILE)


__all__ = [
    "log_interaction",
    "log_suggestion",
    "load_interactions",
    "log_ritual_result",
    "watchdog",
    "INTERACTIONS_FILE",
    "QUARANTINE_FILE",
]
