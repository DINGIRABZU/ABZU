from __future__ import annotations

"""Simple feedback log reader with retraining thresholds."""

from pathlib import Path
import json
import logging
from typing import Any, List

from config import settings

LOG_FILE = Path("data/feedback.json")
NOVELTY_THRESHOLD = settings.feedback_novelty_threshold
COHERENCE_THRESHOLD = settings.feedback_coherence_threshold

logger = logging.getLogger(__name__)


def load_feedback() -> List[dict[str, Any]]:
    """Return all feedback entries from :data:`LOG_FILE`."""
    if not LOG_FILE.exists():
        return []
    try:
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("failed to read %s", LOG_FILE)
        return []


__all__ = [
    "load_feedback",
    "LOG_FILE",
    "NOVELTY_THRESHOLD",
    "COHERENCE_THRESHOLD",
]
