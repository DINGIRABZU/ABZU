"""Dashboard components for monitoring and mixing."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["app", "qnl_mixer", "rl_metrics", "usage", "system_monitor"]


def __getattr__(name: str) -> Any:  # pragma: no cover - simple delegation
    """Dynamically import dashboard submodules on first access."""

    if name in __all__:
        return import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__} has no attribute {name}")
