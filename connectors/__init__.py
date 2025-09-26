"""Communication connectors for Spiral OS."""

from __future__ import annotations

import importlib
import os
from types import MappingProxyType
from typing import Any

__version__ = "0.3.0"

# ``ABZU_USE_MCP`` toggles internal services to communicate via the MCP
# gateway. External connectors continue to use HTTP APIs regardless of this
# flag.
USE_MCP = os.getenv("ABZU_USE_MCP") == "1"

_EXPORTS: dict[str, tuple[str, str]] = {
    "webrtc_router": ("connectors.webrtc_connector", "router"),
    "webrtc_start_call": ("connectors.webrtc_connector", "start_call"),
    "webrtc_close_peers": ("connectors.webrtc_connector", "close_peers"),
    "primordials_send_metrics": ("connectors.primordials_api", "send_metrics"),
    "ConnectorHeartbeat": ("connectors.base", "ConnectorHeartbeat"),
    "narrative_router": ("narrative_api", "router"),
}

_EXPORT_MAP: MappingProxyType[str, tuple[str, str]] = MappingProxyType(_EXPORTS)


def _resolve(name: str) -> Any:
    module_name, attribute = _EXPORT_MAP[name]
    module = importlib.import_module(module_name)
    value = getattr(module, attribute)
    globals()[name] = value
    return value


def __getattr__(name: str) -> Any:
    """Lazily import heavy connector modules on first access."""

    if name in _EXPORT_MAP:
        return _resolve(name)
    raise AttributeError(f"module 'connectors' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose exported attributes for tooling that relies on ``dir()``."""

    return sorted({*globals(), *_EXPORT_MAP})


__all__ = list(_EXPORT_MAP)
