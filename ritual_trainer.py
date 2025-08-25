from __future__ import annotations

"""Fine-tune the model from retrieval insights."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Iterable, List

project_root = Path(__file__).resolve().parent / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import auto_retrain
from core.utils.seed import seed_all
from memory import spiral_cortex

STATE_FILE = Path("data/ritual_trainer_state.json")
THRESHOLD = 10

logger = logging.getLogger(__name__)

seed_all(int(os.getenv("SEED", "0")))


def _load_state() -> int:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("processed", 0)
    except Exception:
        return 0


def _save_state(count: int) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"processed": count}), encoding="utf-8")
    except Exception:
        logger.exception("failed to save state")


def build_dataset(entries: Iterable[dict[str, Any]]) -> List[dict[str, Any]]:
    dataset = []
    for ent in entries:
        snippets = " ".join(s.get("snippet", "") for s in ent.get("snippets", []))
        dataset.append({"prompt": ent.get("question", ""), "completion": snippets})
    return dataset


def run_training(run: bool) -> None:
    entries = spiral_cortex.load_insights()
    processed = _load_state()
    new_entries = entries[processed:]
    if len(new_entries) >= THRESHOLD and auto_retrain.system_idle():
        dataset = build_dataset(new_entries)
        if run:
            auto_retrain.trigger_finetune(dataset)
            _save_state(len(entries))
        else:
            logger.info(json.dumps(dataset, indent=2))
    else:
        logger.info("Conditions not met")


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI entry
    parser = argparse.ArgumentParser(description="Retrain from spiral insights")
    parser.add_argument("--run", action="store_true", help="Execute training")
    args = parser.parse_args(argv)
    run_training(args.run)


if __name__ == "__main__":  # pragma: no cover - manual run
    main()
