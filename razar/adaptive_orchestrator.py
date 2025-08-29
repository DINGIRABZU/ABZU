from __future__ import annotations

__version__ = "0.1.0"

"""Adaptive orchestrator that searches for efficient boot sequences.

The orchestrator reads component priorities from ``component_priorities.yaml`` and
tries several start orders.  Each attempt records the time taken to reach a
"ready" state and any failure points.  Results are appended to
``logs/razar_boot_history.json`` and the quickest sequence is marked as the
current best.

This module is intentionally lightweight.  It does not launch real services but
acts as a scaffold for future integration with the RAZAR runtime manager.
"""

import argparse
import json
import logging
import random
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml
from . import checkpoint_manager

LOGGER = logging.getLogger("razar.adaptive_orchestrator")

ROOT = Path(__file__).resolve().parents[1]
PRIORITY_PATH = ROOT / "docs" / "component_priorities.yaml"
HISTORY_PATH = ROOT / "logs" / "razar_boot_history.json"


def load_priorities(path: Path = PRIORITY_PATH) -> List[str]:
    """Return component names ordered by priority."""

    data: Dict[str, Dict[str, str]] = yaml.safe_load(path.read_text())

    def priority_value(priority: str) -> int:
        try:
            return int(priority.lstrip("P"))
        except Exception:  # pragma: no cover - defensive
            return 999

    ordered = sorted(
        (
            (name, priority_value(info.get("priority", "P999")))
            for name, info in data.items()
        ),
        key=lambda item: item[1],
    )
    return [name for name, _ in ordered]


def generate_sequence(strategy: str, components: List[str]) -> List[str]:
    """Return a boot sequence based on ``strategy``."""

    if strategy == "priority":
        return components.copy()
    shuffled = components.copy()
    random.shuffle(shuffled)
    return shuffled


def run_sequence(sequence: List[str], start_index: int = 0) -> Dict[str, Any]:
    """Simulate running ``sequence`` and gather metrics.

    ``start_index`` indicates how many components in ``sequence`` have already
    completed successfully. After each component starts the current progress is
    written to :mod:`checkpoint_manager` so that an interrupted run can resume.
    """

    start = time.monotonic()
    failures: List[str] = []
    for idx, comp in enumerate(sequence[start_index:], start=start_index):
        LOGGER.info("Starting %s", comp)
        time.sleep(0.01)  # placeholder for real startup
        checkpoint_manager.save_checkpoint(sequence, idx + 1)
    duration = time.monotonic() - start
    checkpoint_manager.clear_checkpoint()
    return {"sequence": sequence, "time_to_ready": duration, "failures": failures}


def is_better(candidate: Dict[str, Any], current: Dict[str, Any] | None) -> bool:
    """Return ``True`` if ``candidate`` is better than ``current``."""

    if current is None:
        return True
    if candidate["failures"] and not current["failures"]:
        return False
    if not candidate["failures"] and current["failures"]:
        return True
    return candidate["time_to_ready"] < current["time_to_ready"]


def load_history(path: Path = HISTORY_PATH) -> Dict[str, Any]:
    """Load history JSON if it exists."""

    if path.exists():
        return json.loads(path.read_text())
    return {"history": [], "best": None}


def save_history(history: Dict[str, Any], path: Path = HISTORY_PATH) -> None:
    """Persist ``history`` to ``path``."""

    path.write_text(json.dumps(history, indent=2))


def main() -> None:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description="Adaptive RAZAR boot orchestrator")
    parser.add_argument(
        "--strategy",
        choices=["priority", "random"],
        default="priority",
        help="Sequence generation strategy",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from best-known sequence",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    random.seed(42)

    components = load_priorities()
    history = load_history()

    checkpoint = checkpoint_manager.load_checkpoint()
    if checkpoint:
        seq = checkpoint.get("sequence", [])
        start = int(checkpoint.get("last_success", 0))
        if seq:
            record = run_sequence(seq, start)
            history["history"].append(record)
            if is_better(record, history.get("best")):
                history["best"] = record
            save_history(history)
            return

    sequences: List[List[str]] = []
    if args.resume and history.get("best"):
        sequences.append(history["best"]["sequence"])
    else:
        sequences.append(generate_sequence(args.strategy, components))
    while len(sequences) < 3:
        sequences.append(generate_sequence("random", components))

    for seq in sequences:
        record = run_sequence(seq)
        history["history"].append(record)
        if is_better(record, history.get("best")):
            history["best"] = record

    save_history(history)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
