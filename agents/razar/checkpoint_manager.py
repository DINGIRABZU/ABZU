from __future__ import annotations

"""Simple checkpoint manager for RAZAR components.

The manager persists boot progress in ``logs/razar_state.json`` so the runtime
manager can resume from the last successful component after a failure. Each
successful component name is appended to a ``history`` list alongside the
``last_component`` field.  Checkpoints can be cleared to restart from the
beginning.
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
    """Persist ``name`` as the last successful component.

    The checkpoint file stores two fields:

    - ``last_component`` – the most recently successful component.
    - ``history`` – ordered list of all successful component names.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    history: list[str] = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            history = list(data.get("history", []))
        except json.JSONDecodeError:  # pragma: no cover - corrupted state
            history = []
    history.append(name)
    path.write_text(
        json.dumps({"last_component": name, "history": history}),
        encoding="utf-8",
    )


def clear_checkpoint(path: Path = DEFAULT_PATH) -> None:
    """Remove the checkpoint file if it exists."""

    if path.exists():
        path.unlink()
