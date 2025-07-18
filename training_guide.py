from __future__ import annotations

"""Log intent outcomes for reinforcement learning.

Entries are appended to ``data/feedback.json`` as dictionaries with the
following keys:
``timestamp`` ISO‑8601 time of the event,
``intent`` intent name,
``action`` handler action name,
``tone`` tonal label if provided,
``success`` boolean result indicator.
"""

from pathlib import Path
from datetime import datetime
import json
import os

from INANNA_AI import db_storage
import auto_retrain

AUTO_RETRAIN_THRESHOLD = int(os.getenv("RETRAIN_THRESHOLD", "10"))


def evaluate_action(intent: dict, result: dict) -> dict:
    """Return evaluation metrics for the executed ``intent``.

    Parameters
    ----------
    intent:
        Intent dictionary describing the action.
    result:
        Dictionary returned by the handler containing at least ``text``.

    Returns
    -------
    dict
        Mapping with ``response_quality`` and ``memory_overlap`` scores.
    """

    text = str(result.get("text", ""))
    words = text.split()
    coherence = len(set(words)) / len(words) if words else 0.0

    intent_words = str(intent.get("intent", "")).split()
    src = set(intent_words)
    gen = set(words)
    relevance = len(src & gen) / len(src | gen) if src and gen else 0.0
    quality = (coherence + relevance) / 2.0

    overlap = 0.0
    try:  # pragma: no cover - optional logging file may not exist
        from corpus_memory_logging import load_interactions

        interactions = load_interactions(limit=5)
        if interactions and gen:
            scores = []
            for entry in interactions:
                prev = set(str(entry.get("input", "")).split())
                if not prev:
                    continue
                scores.append(len(prev & gen) / len(prev | gen))
            if scores:
                overlap = sum(scores) / len(scores)
    except Exception:
        overlap = 0.0

    return {
        "response_quality": round(quality, 3),
        "memory_overlap": round(overlap, 3),
    }

FEEDBACK_FILE = Path("data/feedback.json")


def _count_new_insights(entries: list[dict]) -> int:
    """Return number of unique intents not present in the insight matrix."""
    try:
        insights = json.loads(auto_retrain.INSIGHT_FILE.read_text(encoding="utf-8"))
    except Exception:
        insights = {}
    known = set(insights)
    intents = {e.get("intent") for e in entries if e.get("intent")}
    return len(intents - known)


def _load_entries() -> list[dict]:
    if FEEDBACK_FILE.exists():
        try:
            return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def log_result(
    intent: dict, success: bool, tone: str | None, result: dict | None = None
) -> None:
    """Append ``intent`` outcome to the feedback log."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "intent": intent.get("intent"),
        "action": intent.get("action"),
        "tone": tone,
        "success": bool(success),
    }
    if result is not None:
        entry.update(evaluate_action(intent, result))
    entries = _load_entries()
    entries.append(entry)
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    score = 1.0 if success else 0.0
    db_storage.log_feedback(tone or "neutral", score, score, score)

    if _count_new_insights(entries) >= AUTO_RETRAIN_THRESHOLD:
        auto_retrain.main(["--run"])

