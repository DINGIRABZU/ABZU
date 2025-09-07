"""Communication connectors for Spiral OS."""

from __future__ import annotations

import os

__version__ = "0.3.0"

# ``ABZU_USE_MCP`` toggles internal services to communicate via the MCP
# gateway. External connectors continue to use HTTP APIs regardless of this
# flag.
USE_MCP = os.getenv("ABZU_USE_MCP") == "1"

from .webrtc_connector import close_peers as webrtc_close_peers
from .webrtc_connector import router as webrtc_router
from .webrtc_connector import start_call as webrtc_start_call
from .primordials_api import send_metrics as primordials_send_metrics
from .base import ConnectorHeartbeat
from narrative_api import router as narrative_router

__all__ = [
    "webrtc_router",
    "webrtc_start_call",
    "webrtc_close_peers",
    "primordials_send_metrics",
    "narrative_router",
    "ConnectorHeartbeat",
]
