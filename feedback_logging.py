from __future__ import annotations

"""Simple feedback log reader with retraining thresholds."""

from pathlib import Path
import json
import logging
import os
from typing import Any, List

LOG_FILE = Path("data/feedback.json")
NOVELTY_THRESHOLD = float(os.getenv("FEEDBACK_NOVELTY_THRESHOLD", "0.3"))
COHERENCE_THRESHOLD = float(os.getenv("FEEDBACK_COHERENCE_THRESHOLD", "0.7"))

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
