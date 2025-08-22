"""Compatibility wrappers around :class:`core.task_profiler.TaskProfiler`.

Instantiates a shared profiler at import time for quick access."""

from __future__ import annotations

from typing import Any, Dict

from core.task_profiler import TaskProfiler

_profiler = TaskProfiler()


def classify_task(text: str | Dict[str, Any]) -> str:
    """Return a coarse category for ``text`` or data dict."""
    return _profiler.classify(text)


def ritual_action_sequence(condition: str, emotion: str):
    """Return ritual actions for ``condition`` and ``emotion``."""
    return _profiler.ritual_action_sequence(condition, emotion)


__all__ = ["classify_task", "ritual_action_sequence", "TaskProfiler"]
