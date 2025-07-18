from __future__ import annotations

"""Environment variable validation utilities."""

import importlib
import logging
import os
from typing import Iterable


logger = logging.getLogger(__name__)


def check_required(vars: Iterable[str]) -> None:
    """Ensure that required environment variables are set.

    Parameters
    ----------
    vars:
        Names of environment variables that must be present.

    Raises
    ------
    SystemExit
        If any variable is missing.
    """
    missing = [name for name in vars if not os.getenv(name)]
    if missing:
        plural = "s" if len(missing) > 1 else ""
        names = ", ".join(missing)
        raise SystemExit(f"Missing required environment variable{plural}: {names}")


def check_optional_packages(packages: Iterable[str]) -> None:
    """Log a warning for packages that fail to import."""
    for name in packages:
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - import errors vary
            logger.warning("Optional package %s not available: %s", name, exc)
