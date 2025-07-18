"""Personality layers for INANNA AI."""

from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules
from typing import Dict, Type

from .albedo import AlbedoPersonality

REGISTRY: Dict[str, Type] = {"albedo": AlbedoPersonality}

for mod in iter_modules(__path__):
    if mod.name == "albedo":
        continue
    module = import_module(f"{__name__}.{mod.name}")
    cls = None
    if hasattr(module, "__all__"):
        for name in module.__all__:
            if name.endswith("Personality"):
                cls = getattr(module, name, None)
                if cls:
                    break
    if cls is None:
        for attr in dir(module):
            if attr.endswith("Personality"):
                cls = getattr(module, attr)
                break
    if cls is not None:
        REGISTRY[mod.name] = cls

def list_personalities() -> list[str]:
    """Return available personality layer names sorted alphabetically."""

    return sorted(REGISTRY)


__all__ = ["AlbedoPersonality", "REGISTRY", "list_personalities"]
