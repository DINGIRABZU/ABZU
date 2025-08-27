from __future__ import annotations

"""Simple checkpoint manager for RAZAR components.

The manager persists the name of the last successfully started component so the
runtime manager can resume from that point after a failure. Checkpoints are
stored as JSON files and can be cleared to restart from the beginning.
"""

from pathlib import Path
import json

DEFAULT_PATH = Path("logs/razar_state.json")


def load_checkpoint(path: Path = DEFAULT_PATH) -> str:
    """Return the name of the last successful component if available."""

    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(data.get("last_component", ""))


def save_checkpoint(name: str, path: Path = DEFAULT_PATH) -> None:
    """Persist ``name`` as the last successful component."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_component": name}), encoding="utf-8")


def clear_checkpoint(path: Path = DEFAULT_PATH) -> None:
    """Remove the checkpoint file if it exists."""

    if path.exists():
        path.unlink()
