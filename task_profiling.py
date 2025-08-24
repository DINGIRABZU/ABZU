"""Compatibility wrappers around :class:`core.task_profiler.TaskProfiler`.

Instantiates a shared profiler at import time for quick access.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.task_profiler import TaskProfiler

_profiler = TaskProfiler()


def classify_task(text: str | Dict[str, Any]) -> str:
    """Return a coarse category for ``text`` or data dict."""
    return _profiler.classify(text)


def ritual_action_sequence(condition: str, emotion: str) -> List[str]:
    """Return ritual action names for ``condition`` and ``emotion``.

    Delegates to the shared :class:`TaskProfiler` instance which maps the
    inputs to a sequence of actions defined in the ritual profile.
    """
    return _profiler.ritual_action_sequence(condition, emotion)


__all__ = ["classify_task", "ritual_action_sequence", "TaskProfiler"]
