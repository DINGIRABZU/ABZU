from __future__ import annotations

"""Load Crown agent configuration and expose model endpoints."""

import logging
import os
from pathlib import Path
from typing import Dict

import yaml

from env_validation import parse_servant_models

# Path to the Crown configuration YAML file
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "crown.yml"

# Runtime configuration cache
_RUNTIME_CONFIG: Dict[str, object] = {}

logger = logging.getLogger(__name__)


def load_crown_config() -> Dict[str, object]:
    """Return configuration dictionary merged with ``os.environ`` overrides."""

    cfg: Dict[str, object] = {}
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

    servants = dict(cfg.get("servant_models") or {})
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
    for name, url in (_RUNTIME_CONFIG.get("servant_models") or {}).items():
        if isinstance(url, str):
            endpoints[name] = url
    return endpoints


__all__ = ["load_crown_config", "get_model_endpoints", "_RUNTIME_CONFIG"]
