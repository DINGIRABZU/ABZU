from __future__ import annotations

"""WebRTC signaling server using MediaSoup."""

import logging
from typing import Any

try:  # pragma: no cover - optional dependency
    import mediasoup  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    mediasoup = None  # type: ignore

logger = logging.getLogger(__name__)


class WebRTCServer:
    """Minimal MediaSoup-based SFU server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.worker: Any | None = None
        self.router: Any | None = None

    async def start(self) -> None:
        """Start the MediaSoup worker and router."""
        if mediasoup is None:  # pragma: no cover - optional dependency
            raise RuntimeError("mediasoup library not installed")
        self.worker = await mediasoup.create_worker()
        self.router = await self.worker.create_router({"mediaCodecs": []})
        logger.info("WebRTC server started on %s:%s", self.host, self.port)

    async def stop(self) -> None:
        """Stop the server and release resources."""
        if self.router is not None:
            await self.router.close()
        if self.worker is not None:
            await self.worker.close()
        logger.info("WebRTC server stopped")


__all__ = ["WebRTCServer"]
