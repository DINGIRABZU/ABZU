from __future__ import annotations

"""WebRTC connector for streaming audio files to the browser."""

import asyncio
import logging
from pathlib import Path
from typing import Set

from fastapi import APIRouter, Request
from aiortc import RTCPeerConnection, RTCSessionDescription

logger = logging.getLogger(__name__)

router = APIRouter()
_pcs: Set[RTCPeerConnection] = set()
_channels: Set[any] = set()


@router.post("/call")
async def offer(request: Request) -> dict[str, str]:
    """Handle WebRTC call offer and return the answer."""
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    _pcs.add(pc)

    @pc.on("datachannel")
    def on_datachannel(channel: any) -> None:
        _channels.add(channel)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    logger.info("WebRTC call peer connected")
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


async def close_peers() -> None:
    """Close all peer connections."""
    coros = [pc.close() for pc in list(_pcs)]
    _pcs.clear()
    _channels.clear()
    await asyncio.gather(*coros, return_exceptions=True)


async def _send_audio(path: Path) -> None:
    if not _channels:
        return
    try:
        data = path.read_bytes()
    except Exception as exc:  # pragma: no cover - safeguard
        logger.error("failed to read audio: %s", exc)
        return
    for ch in list(_channels):
        try:
            await ch.send(data)
        except Exception as exc:  # pragma: no cover - transmission may fail
            logger.warning("failed to send audio: %s", exc)
            _channels.discard(ch)


def start_call(path: str) -> None:
    """Schedule sending ``path`` to connected peers."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("start_call called without event loop")
        return
    loop.create_task(_send_audio(Path(path)))


__all__ = ["router", "close_peers", "start_call"]
