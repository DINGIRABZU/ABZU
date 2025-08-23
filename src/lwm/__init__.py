from __future__ import annotations

"""Large World Model package."""

from .config_model import LWMConfig, load_config
from .large_world_model import LargeWorldModel

# Default instance used by media generation and introspection routes.
default_lwm = LargeWorldModel()

__all__ = ["LargeWorldModel", "default_lwm", "LWMConfig", "load_config"]
