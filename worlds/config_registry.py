"""Central registry for per-world configuration metadata."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, DefaultDict

# Internal structure:
# {_world: {"layers": set(), "agents": set(), "brokers": {}, "paths": {}}}
_registry: DefaultDict[str, Dict[str, Any]] = defaultdict(
    lambda: {"layers": set(), "agents": set(), "brokers": {}, "paths": {}}
)


def _world_name(world: str | None = None) -> str:
    """Return normalised world name.

    When ``world`` is ``None`` the ``WORLD_NAME`` environment variable is used
    falling back to ``"default"``.
    """

    return world or os.getenv("WORLD_NAME", "default")


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


def export_config(world: str | None = None) -> Dict[str, Any]:
    """Return a JSON-serialisable mapping for ``world``."""

    data = _registry[_world_name(world)]
    return {
        "layers": sorted(data["layers"]),
        "agents": sorted(data["agents"]),
        "brokers": dict(data["brokers"]),
        "paths": dict(data["paths"]),
    }


def import_config(config: Dict[str, Any], world: str | None = None) -> None:
    """Merge ``config`` into the registry for ``world``."""

    data = _registry[_world_name(world)]
    data["layers"].update(config.get("layers", []))
    data["agents"].update(config.get("agents", []))
    data["brokers"].update(config.get("brokers", {}))
    data["paths"].update(config.get("paths", {}))


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
    "export_config",
    "import_config",
    "export_config_file",
    "import_config_file",
    "reset_registry",
]
