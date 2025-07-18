from __future__ import annotations

"""Automatically trigger fine-tuning based on feedback metrics."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Iterable, List, Dict

import feedback_logging
import vector_memory

INSIGHT_FILE = Path("insight_matrix.json")

NOVELTY_THRESHOLD = feedback_logging.NOVELTY_THRESHOLD
COHERENCE_THRESHOLD = feedback_logging.COHERENCE_THRESHOLD


logger = logging.getLogger(__name__)


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("failed to load %s", path)
        return default


def compute_metrics(insights: dict, feedback: Iterable[dict]) -> tuple[float, float]:
    """Return novelty and coherence scores from feedback."""
    try:
        entries = list(feedback)
        if not entries:
            return 0.0, 0.0

        known = set(insights)
        intents = [e.get("intent") for e in entries if e.get("intent")]
        new = sum(1 for i in intents if i not in known)
        novelty = new / len(intents) if intents else 0.0

        scores = [e.get("response_quality", 0.0) for e in entries]
        coherence = sum(scores) / len(scores) if scores else 0.0
        return novelty, coherence
    except Exception:
        logger.exception("failed to compute metrics")
        return 0.0, 0.0


def build_dataset(feedback: Iterable[dict]) -> list[dict]:
    """Return a fine-tuning dataset from successful feedback entries."""
    try:
        dataset = []
        for entry in feedback:
            if (
                entry.get("success")
                and entry.get("intent")
                and entry.get("action")
            ):
                dataset.append({
                    "prompt": entry["intent"],
                    "completion": entry["action"],
                })
        return dataset
    except Exception:
        logger.exception("failed to build dataset")
        return []


def _load_vector_logs() -> List[Dict[str, Any]]:
    if not vector_memory.LOG_FILE.exists():
        return []
    entries = []
    with vector_memory.LOG_FILE.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                entries.append(json.loads(line))
            except Exception:
                logger.error("invalid json line in %s", vector_memory.LOG_FILE)
    return entries


def system_idle() -> bool:
    """Return ``True`` if no training lock file exists."""
    return not Path("training.lock").exists()


def trigger_finetune(dataset: list[dict]) -> None:
    """Invoke the LLM fine-tuning API with ``dataset``."""
    try:
        import llm_api

        llm_api.fine_tune(dataset)
    except Exception:
        logger.exception("failed to trigger fine-tune")


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI entry
    parser = argparse.ArgumentParser(description="Automatically retrain model")
    parser.add_argument("--run", action="store_true", help="Execute fine-tuning")
    parser.add_argument("--dry-run", action="store_true", help="Show dataset only")
    args = parser.parse_args(argv)

    insights = _load_json(INSIGHT_FILE, {})
    feedback = feedback_logging.load_feedback()
    vector_entries = _load_vector_logs()

    novelty, coherence = compute_metrics(insights, feedback)
    logger.info("Novelty: %.2f Coherence: %.2f", novelty, coherence)

    if (
        novelty >= NOVELTY_THRESHOLD
        and coherence >= COHERENCE_THRESHOLD
        and vector_entries
        and system_idle()
    ):
        dataset = build_dataset(feedback)
        if args.run:
            trigger_finetune(dataset)
            logger.info("Fine-tuning triggered")
        else:
            logger.info(json.dumps(dataset, indent=2))
    else:
        logger.info("Conditions not met")


if __name__ == "__main__":  # pragma: no cover - manual run
    main()
