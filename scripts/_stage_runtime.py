"""Runtime helpers for Stage automation scripts."""

from __future__ import annotations

import importlib
import sys
import warnings
from pathlib import Path
from typing import Iterable

__all__ = ["EnvironmentLimitedWarning", "bootstrap"]


class EnvironmentLimitedWarning(UserWarning):
    """Warning emitted when optional modules are unavailable in the sandbox."""


def _detect_repo_root(start: Path | None = None) -> Path:
    """Heuristically locate the repository root from ``start``."""

    path = (start or Path(__file__)).resolve()
    for candidate in [path, *path.parents]:
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    return path.parent


def _ensure_path(path: Path) -> None:
    """Insert ``path`` at the front of :data:`sys.path` if missing."""

    resolved = str(path)
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def bootstrap(optional_modules: Iterable[str] | None = None) -> Path:
    """Prepare the Stage runtime and return the repository root."""

    root = _detect_repo_root()
    _ensure_path(root)

    src_dir = root / "src"
    if src_dir.exists():
        _ensure_path(src_dir)

    for name in optional_modules or ():
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - module import errors vary
            message = (
                "environment-limited: unable to import optional module"
                f" '{name}': {exc}"
            )
            warnings.warn(
                message,
                EnvironmentLimitedWarning,
                stacklevel=2,
            )

    return root
