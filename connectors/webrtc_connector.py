"""WebRTC connector for streaming data, audio, and video.

Configuration flags (``ENABLE_DATA``, ``ENABLE_AUDIO``, ``ENABLE_VIDEO``)
toggle corresponding streams. Track helpers from
``communication.webrtc_server`` gracefully return ``None`` when disabled or
unavailable, allowing clients to fall back to data-only operation.
"""

from __future__ import annotations

__version__ = "0.3.1"

import asyncio
import logging
from pathlib import Path
from typing import Set

from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi import APIRouter, HTTPException, Request

from communication.webrtc_server import get_audio_track, get_video_track

logger = logging.getLogger(__name__)

router = APIRouter()
_pcs: Set[RTCPeerConnection] = set()
_channels: Set[any] = set()

# Configuration flags -----------------------------------------------------
ENABLE_DATA = True
ENABLE_AUDIO = True
ENABLE_VIDEO = True


def configure(*, data: bool = True, audio: bool = True, video: bool = True) -> None:
    """Configure which streams are offered to peers."""
    global ENABLE_DATA, ENABLE_AUDIO, ENABLE_VIDEO
    ENABLE_DATA = data
    ENABLE_AUDIO = audio
    ENABLE_VIDEO = video


@router.post("/call")
async def offer(request: Request) -> dict[str, str]:
    """Handle WebRTC call offer and return the answer."""
    try:
        params = await request.json()
        sdp = params["sdp"]
        typ = params["type"]
    except Exception as exc:  # pragma: no cover - invalid payload
        logger.error("invalid offer payload: %s", exc)
        raise HTTPException(status_code=400, detail="invalid offer") from exc
    offer = RTCSessionDescription(sdp=sdp, type=typ)

    pc = RTCPeerConnection()
    _pcs.add(pc)

    if ENABLE_DATA:

        @pc.on("datachannel")
        def on_datachannel(channel: any) -> None:
            _channels.add(channel)

    has_audio = "m=audio" in offer.sdp
    has_video = "m=video" in offer.sdp
    if ENABLE_VIDEO and has_video:
        track = get_video_track()
        if track is not None:
            pc.addTrack(track)
    if ENABLE_AUDIO and has_audio:
        track = get_audio_track()
        if track is not None:
            pc.addTrack(track)

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
    if not (ENABLE_DATA and _channels):
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


def start_stream(path: str) -> None:
    """Schedule sending ``path`` to connected peers over the data channel."""
    if not ENABLE_DATA:
        logger.debug("data channel disabled; start_stream ignored")
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("start_stream called without event loop")
        return
    loop.create_task(_send_audio(Path(path)))


# Backwards compatible alias ------------------------------------------------
start_call = start_stream


__all__ = ["router", "close_peers", "start_stream", "start_call", "configure"]
