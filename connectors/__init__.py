"""Communication connectors for Spiral OS."""

from __future__ import annotations

__version__ = "0.3.0"

from .webrtc_connector import close_peers as webrtc_close_peers
from .webrtc_connector import router as webrtc_router
from .webrtc_connector import start_call as webrtc_start_call
from .primordials_api import send_metrics as primordials_send_metrics

__all__ = [
    "webrtc_router",
    "webrtc_start_call",
    "webrtc_close_peers",
    "primordials_send_metrics",
]
