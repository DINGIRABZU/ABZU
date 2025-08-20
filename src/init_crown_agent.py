from __future__ import annotations

"""Load Crown agent configuration and expose model endpoints."""

from pathlib import Path
import os
from typing import Dict

import yaml

# Path to the Crown configuration YAML file
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "crown.yml"

# Runtime configuration cache
_RUNTIME_CONFIG: Dict[str, object] = {}


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
    env_servants = os.getenv("SERVANT_MODELS")
    if env_servants:
        for item in env_servants.split(","):
            name, _, url = item.partition("=")
            if name and url:
                servants[name.strip()] = url.strip()
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
