"""Download and load remote RAZAR agents at runtime.

This utility fetches Python modules over HTTP, caches them locally and
loads them with :mod:`importlib`.  Each remote agent is expected to expose a
``configure()`` function which returns a dictionary of its runtime parameters.
Returned configurations are persisted to ``logs/razar_remote_agents.json`` for
auditability.
"""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Tuple

import requests

logger = logging.getLogger(__name__)

# Directory to cache downloaded agent modules
CACHE_DIR = Path(__file__).resolve().parent / "_remote_cache"
# Path to configuration log
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "razar_remote_agents.json"


def _download(url: str, dest: Path) -> None:
    """Download ``url`` into ``dest``."""

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(response.text, encoding="utf-8")


def _persist_config(name: str, config: Dict[str, Any]) -> None:
    """Store ``config`` for ``name`` in the audit log."""

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: Dict[str, Any] = {}
    if LOG_PATH.exists():
        try:
            data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Could not decode %s; starting fresh", LOG_PATH)
    data[name] = config
    LOG_PATH.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def load_remote_agent(
    name: str, url: str, *, refresh: bool = False
) -> Tuple[ModuleType, Dict[str, Any]]:
    """Return the remote agent module and its configuration.

    Parameters
    ----------
    name:
        Module name for the downloaded agent.
    url:
        HTTP(S) location of the Python source file.
    refresh:
        If ``True``, the module is downloaded even if a cached copy exists.
    """

    path = CACHE_DIR / f"{name}.py"
    if refresh or not path.exists():
        logger.info("Downloading agent %s from %s", name, url)
        _download(url, path)

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import agent {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    config: Dict[str, Any] = {}
    configure = getattr(module, "configure", None)
    if callable(configure):
        try:
            result = configure()
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.error("configure() for %s raised %s", name, exc)
        else:
            if isinstance(result, dict):
                config = result
                _persist_config(name, config)
            else:
                logger.warning("configure() for %s did not return a dict", name)
    else:
        logger.warning("Agent %s missing configure() function", name)

    return module, config
