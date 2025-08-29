"""Checkpoint utilities for the adaptive orchestrator.

The checkpoint stores the component sequence, per-component states and the
index of the next component to start. It allows the orchestrator to resume a
partially completed run after a crash or manual interruption.
"""

__version__ = "0.1.0"

from pathlib import Path
import json
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = ROOT / "logs" / "razar_checkpoint.json"


def load_checkpoint(path: Path = CHECKPOINT_PATH) -> Dict[str, Any] | None:
    """Return checkpoint data if available.

    The checkpoint file contains a ``sequence`` list of component names,
    ``last_success`` index and a mapping of component ``states``.
    ``None`` is returned when the checkpoint does not exist or is invalid.
    """

    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_checkpoint(
    sequence: List[str], last_success: int, path: Path = CHECKPOINT_PATH
) -> None:
    """Persist ``sequence`` and ``last_success`` to ``path``.

    ``last_success`` denotes the index of the next component to start. All
    components with an index lower than this value are marked ``started`` in the
    checkpoint ``states`` dictionary; the remaining components are marked
    ``pending``.
    """

    states = {
        name: ("started" if idx < last_success else "pending")
        for idx, name in enumerate(sequence)
    }
    data = {"sequence": sequence, "last_success": last_success, "states": states}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_checkpoint(path: Path = CHECKPOINT_PATH) -> None:
    """Remove the checkpoint file if it exists."""

    if path.exists():
        path.unlink()
