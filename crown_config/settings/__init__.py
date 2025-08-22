"""Utilities for reading optional layer configuration.

This package loads a YAML file describing enabled personality layers and
exposes helpers for querying that state. Import time triggers a disk read to
populate the cached configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent / "layers.yaml"


def load_layer_config() -> Dict[str, bool]:
    """Load layer enablement flags from :data:`_CONFIG_PATH`."""
    if _CONFIG_PATH.exists():
        try:
            data = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                layers = data.get("layers", {})
                if isinstance(layers, dict):
                    return {str(k): bool(v) for k, v in layers.items()}
        except Exception:
            return {}
    return {}


_LAYERS = load_layer_config()


def is_layer_enabled(name: str) -> bool:
    """Return ``True`` if the layer ``name`` is enabled or unknown."""
    return _LAYERS.get(name, True)


__all__ = ["is_layer_enabled", "load_layer_config"]
