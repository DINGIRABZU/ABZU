"""Central registry for per-world configuration metadata."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, DefaultDict

# Internal structure:
# {
#   _world: {
#       "layers": set(),
#       "agents": set(),
#       "brokers": {},
#       "paths": {},
#       "model_paths": {},
#       "remote_attempts": {},
#       "component_hashes": {},
#       "patches": [],
#       "model_endpoints": {},
#   }
# }
_registry: DefaultDict[str, Dict[str, Any]] = defaultdict(
    lambda: {
        "layers": set(),
        "agents": set(),
        "brokers": {},
        "paths": {},
        "model_paths": {},
        "remote_attempts": {},
        "component_hashes": {},
        "patches": [],
        "model_endpoints": {},
    }
)


def _world_name(world: str | None = None) -> str:
    """Return normalised world name.

    When ``world`` is ``None`` the ``WORLD_NAME`` environment variable is used
    falling back to ``"default"``.
    """
    if world is not None:
        return world
    return os.getenv("WORLD_NAME", "default")


def initialize_world(
    layers: list[str] | None = None,
    agents: list[str] | None = None,
    world: str | None = None,
) -> None:
    """Register ``layers`` and ``agents`` for ``world`` in a single step.

    The function is a convenience for bootstrapping new worlds. Missing lists are
    ignored, allowing either ``layers`` or ``agents`` to be provided
    independently.
    """

    for layer in layers or []:
        register_layer(layer, world)
    for agent in agents or []:
        register_agent(agent, world)


def register_layer(layer: str, world: str | None = None) -> None:
    """Record availability of ``layer`` for ``world``."""

    _registry[_world_name(world)]["layers"].add(layer)


def register_agent(agent: str, world: str | None = None) -> None:
    """Record availability of ``agent`` for ``world``."""

    _registry[_world_name(world)]["agents"].add(agent)


def register_broker(
    broker: str, config: Dict[str, Any], world: str | None = None
) -> None:
    """Record ``broker`` configuration for ``world``."""

    _registry[_world_name(world)]["brokers"][broker] = config


def register_path(name: str, path: str, world: str | None = None) -> None:
    """Record filesystem ``path`` identified by ``name`` for ``world``."""

    _registry[_world_name(world)]["paths"][name] = path


def register_model_path(model: str, path: str, world: str | None = None) -> None:
    """Record filesystem ``path`` for ``model`` within ``world``."""

    _registry[_world_name(world)]["model_paths"][model] = path


def register_remote_attempt(component: str, world: str | None = None) -> None:
    """Increment remote repair attempt counter for ``component``."""

    data = _registry[_world_name(world)]["remote_attempts"]
    data[component] = data.get(component, 0) + 1


def register_model_endpoint(
    model: str, endpoint: str, world: str | None = None
) -> None:
    """Record ``endpoint`` for ``model`` within ``world``."""

    _registry[_world_name(world)]["model_endpoints"][model] = endpoint


def register_component_hash(
    component: str, digest: str, world: str | None = None
) -> None:
    """Record final code hash ``digest`` for ``component``."""

    _registry[_world_name(world)]["component_hashes"][component] = digest


def register_patch(
    component: str, patch: str, digest: str, world: str | None = None
) -> None:
    """Record ``patch`` applied to ``component`` with resulting ``digest``."""

    data = _registry[_world_name(world)]
    data["patches"].append({"component": component, "patch": patch, "hash": digest})
    data["component_hashes"][component] = digest


def export_config(world: str | None = None) -> Dict[str, Any]:
    """Return a JSON-serialisable mapping for ``world``."""

    data = _registry[_world_name(world)]
    return {
        "layers": sorted(data["layers"]),
        "agents": sorted(data["agents"]),
        "brokers": dict(data["brokers"]),
        "paths": dict(data["paths"]),
        "model_paths": dict(data["model_paths"]),
        "remote_attempts": dict(data["remote_attempts"]),
        "component_hashes": dict(data["component_hashes"]),
        "patches": list(data["patches"]),
        "model_endpoints": dict(data["model_endpoints"]),
    }


def import_config(config: Dict[str, Any], world: str | None = None) -> None:
    """Merge ``config`` into the registry for ``world``."""

    data = _registry[_world_name(world)]
    data["layers"].update(config.get("layers", []))
    data["agents"].update(config.get("agents", []))
    data["brokers"].update(config.get("brokers", {}))
    data["paths"].update(config.get("paths", {}))
    data["model_paths"].update(config.get("model_paths", {}))
    data["remote_attempts"].update(config.get("remote_attempts", {}))
    data["component_hashes"].update(config.get("component_hashes", {}))
    data["patches"].extend(config.get("patches", []))
    data["model_endpoints"].update(config.get("model_endpoints", {}))


def export_config_file(path: str | Path, world: str | None = None) -> Path:
    """Write configuration for ``world`` to ``path`` in JSON format.

    Returns the path to which the configuration was written.
    """

    p = Path(path)
    p.write_text(json.dumps(export_config(world), indent=2, sort_keys=True), "utf-8")
    return p


def import_config_file(path: str | Path, world: str | None = None) -> None:
    """Load configuration for ``world`` from JSON ``path``."""

    p = Path(path)
    import_config(json.loads(p.read_text("utf-8")), world)


def reset_registry() -> None:
    """Clear all stored world configuration (primarily for tests)."""

    _registry.clear()


__all__ = [
    "register_layer",
    "register_agent",
    "register_broker",
    "register_path",
    "register_model_path",
    "register_remote_attempt",
    "register_component_hash",
    "register_model_endpoint",
    "register_patch",
    "export_config",
    "import_config",
    "export_config_file",
    "import_config_file",
    "reset_registry",
    "initialize_world",
]
