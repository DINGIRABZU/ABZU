"""Utilities for loading optional audio backends."""

from __future__ import annotations

__version__ = "0.1.0"

import importlib
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=None)
def load_backend(name: str) -> Any | None:
    """Return imported module ``name`` or ``None`` if unavailable.

    Parameters
    ----------
    name:
        Module path to import.

    Returns
    -------
    module | None
        The imported module instance, or ``None`` when the import fails.
    """
    try:
        return importlib.import_module(name)
    except Exception:
        return None
