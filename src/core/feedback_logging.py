"""Manage feedback logs and thresholds with on-disk persistence."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, cast

from crown_config import settings

LOG_FILE = Path("data/feedback.json")
NOVELTY_THRESHOLD = settings.feedback_novelty_threshold
COHERENCE_THRESHOLD = settings.feedback_coherence_threshold

logger = logging.getLogger(__name__)


def load_feedback() -> List[dict[str, Any]]:
    """Return all feedback entries from :data:`LOG_FILE`."""
    if not LOG_FILE.exists():
        return []
    try:
        return cast(List[dict[str, Any]], json.loads(LOG_FILE.read_text(encoding="utf-8")))
    except Exception:
        logger.exception("failed to read %s", LOG_FILE)
        return []


def append_feedback(entry: dict[str, Any]) -> None:
    """Append ``entry`` to :data:`LOG_FILE` with a timestamp."""
    try:
        entries = load_feedback()
        entry = {"timestamp": datetime.utcnow().isoformat(), **entry}
        entries.append(entry)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        logger.info("logged feedback to %s", LOG_FILE)
    except Exception:
        logger.exception("failed to append feedback")


__all__ = [
    "load_feedback",
    "append_feedback",
    "LOG_FILE",
    "NOVELTY_THRESHOLD",
    "COHERENCE_THRESHOLD",
]
