from __future__ import annotations

"""Utilities for recording agent communications."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

_LOG_PATH = Path("logs") / "agent_interactions.jsonl"


def log_agent_interaction(entry: Dict[str, Any]) -> None:
    """Append ``entry`` with timestamp to the interactions log."""
    entry = dict(entry)
    entry.setdefault("timestamp", datetime.utcnow().isoformat())
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=repr) + "\n")
