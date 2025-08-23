"""Load Crown agent configuration and expose model endpoints."""

from __future__ import annotations

import importlib.util as _importlib_util
import logging
import os
from pathlib import Path
from typing import Any, Dict, cast

import yaml  # type: ignore[import-untyped]

from env_validation import parse_servant_models

# Path to the Crown configuration YAML file
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "crown.yml"

# Runtime configuration cache
_RUNTIME_CONFIG: Dict[str, Any] = {}

logger = logging.getLogger(__name__)


def load_crown_config() -> Dict[str, object]:
    """Return configuration dictionary merged with ``os.environ`` overrides."""

    cfg: Dict[str, Any] = {}
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh) or {}

    env_map = {
        "glm_api_url": "GLM_API_URL",
        "glm_api_key": "GLM_API_KEY",
        "model_path": "MODEL_PATH",
        "memory_dir": "MEMORY_DIR",
    }
    for key, env in env_map.items():
        val = os.getenv(env)
        if val:
            cfg[key] = val

    servants = dict(cast(Dict[str, str], cfg.get("servant_models") or {}))
    env_servants = parse_servant_models(require=True)
    for name, url in env_servants.items():
        if name in servants:
            logger.warning(
                "Duplicate servant model name '%s' in SERVANT_MODELS; keeping existing",
                name,
            )
            continue
        servants[name] = url
    if servants:
        cfg["servant_models"] = servants

    _RUNTIME_CONFIG.clear()
    _RUNTIME_CONFIG.update(cfg)
    return cfg


def get_model_endpoints() -> Dict[str, str]:
    """Return a mapping of active model names to their URLs."""

    if not _RUNTIME_CONFIG:
        load_crown_config()
    endpoints: Dict[str, str] = {}
    glm_url = _RUNTIME_CONFIG.get("glm_api_url")
    if isinstance(glm_url, str):
        endpoints["glm"] = glm_url
    for name, url in cast(
        Dict[str, Any], _RUNTIME_CONFIG.get("servant_models") or {}
    ).items():
        if isinstance(url, str):
            endpoints[name] = url
    return endpoints


# ---------------------------------------------------------------------------
# Legacy initialisation helper

#
# Some modules import :mod:`init_crown_agent` expecting the richer API provided
# by the top‑level ``init_crown_agent.py``.  The lightweight version in
# ``src/`` originally only exposed configuration helpers which caused imports to
# fail during test collection.  To maintain compatibility we load the root
# module under an internal name and re‑export the key functions here.
_ROOT_PATH = Path(__file__).resolve().parent.parent / "init_crown_agent.py"


_spec = _importlib_util.spec_from_file_location("_init_crown_agent_root", _ROOT_PATH)
assert _spec is not None and _spec.loader is not None
_root = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_root)

initialize_crown = _root.initialize_crown
_init_servants = getattr(_root, "_init_servants")
_check_glm = getattr(_root, "_check_glm")
vector_memory = getattr(_root, "vector_memory")
corpus_memory = getattr(_root, "corpus_memory")

__all__ = [
    "load_crown_config",
    "get_model_endpoints",
    "initialize_crown",
    "_init_servants",
    "_check_glm",
    "vector_memory",
    "corpus_memory",
    "_RUNTIME_CONFIG",
]
