"""No-op mental layer used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict, List


def init_rl_model() -> None:
    """Fallback initializer that does nothing."""


def record_task_flow(
    task_id: str, context: Dict[str, Any], reward: float = 0.0
) -> None:
    """Fallback logger that discards task flows."""


def query_related_tasks(task_id: str) -> List[str]:
    """Return an empty list as no tasks are stored."""
    return []


__all__ = ["init_rl_model", "record_task_flow", "query_related_tasks"]
