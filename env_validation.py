from __future__ import annotations

"""Environment variable validation utilities."""

import importlib
import logging
import os
from typing import Dict, Iterable


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


def parse_servant_models(env: str | None = None, *, require: bool = False) -> Dict[str, str]:
    """Return a mapping parsed from ``SERVANT_MODELS``.

    Parameters
    ----------
    env:
        Optional raw value of ``SERVANT_MODELS``. If omitted, ``os.environ`` is
        consulted.
    require:
        When ``True`` and ``SERVANT_MODELS`` is set but no valid ``name=url``
        pairs are found, :class:`SystemExit` is raised.

    Returns
    -------
    dict
        Mapping of servant names to URLs.
    """

    if env is None:
        env = os.getenv("SERVANT_MODELS")

    servants: Dict[str, str] = {}
    if not env:
        return servants

    for item in env.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            logger.warning(
                "Skipping malformed SERVANT_MODELS entry '%s'; expected name=url",
                item,
            )
            continue
        name, url = item.split("=", 1)
        name = name.strip()
        url = url.strip()
        if not name or not url:
            logger.warning(
                "Skipping malformed SERVANT_MODELS entry '%s'; expected name=url",
                item,
            )
            continue
        if name in servants:
            logger.warning(
                "Duplicate servant model name '%s' in SERVANT_MODELS; keeping first",
                name,
            )
            continue
        servants[name] = url

    if require and env and not servants:
        raise SystemExit(
            "SERVANT_MODELS is set but contains no valid name=url pairs"
        )

    return servants
