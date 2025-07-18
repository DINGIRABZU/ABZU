from __future__ import annotations

"""WebRTC streaming of avatar frames."""

import asyncio
import fractions
import logging
import time
from pathlib import Path
from typing import Optional, Set

import numpy as np
import soundfile as sf

from fastapi import APIRouter, Request
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.mediastreams import AudioStreamTrack, AUDIO_PTIME, MediaStreamError
from av import VideoFrame
from av.audio.frame import AudioFrame

from core import video_engine, avatar_expression_engine

logger = logging.getLogger(__name__)

router = APIRouter()
_pcs: Set[RTCPeerConnection] = set()


class AvatarAudioTrack(AudioStreamTrack):
    """Audio track streaming a WAV file."""

    def __init__(self, audio_path: Optional[Path] = None) -> None:
        super().__init__()
        if audio_path is not None:
            data, self._sr = sf.read(str(audio_path), dtype="int16")
            if data.ndim > 1:
                data = data.mean(axis=1)
            self._data = data.astype("int16")
        else:
            self._sr = 8000
            self._data = np.zeros(0, dtype="int16")
        self._index = 0
        self._samples = int(AUDIO_PTIME * self._sr)
        self._start: float | None = None
        self._timestamp = 0

    async def recv(self) -> AudioFrame:
        if self.readyState != "live":
            raise MediaStreamError

        if self._start is None:
            self._start = time.time()
            self._timestamp = 0
        else:
            self._timestamp += self._samples
            wait = self._start + (self._timestamp / self._sr) - time.time()
            await asyncio.sleep(wait)

        end = self._index + self._samples
        chunk = self._data[self._index:end]
        self._index = end
        if len(chunk) < self._samples:
            chunk = np.pad(chunk, (0, self._samples - len(chunk)), constant_values=0)

        frame = AudioFrame.from_ndarray(chunk.reshape(1, -1), format="s16", layout="mono")
        frame.pts = self._timestamp
        frame.sample_rate = self._sr
        frame.time_base = fractions.Fraction(1, self._sr)
        return frame


class AvatarVideoTrack(VideoStreamTrack):
    """Video track producing frames from ``avatar_expression_engine``."""

    def __init__(self, audio_path: Optional[Path] = None) -> None:
        super().__init__()
        if audio_path is not None:
            self._frames = avatar_expression_engine.stream_avatar_audio(audio_path)
        else:
            self._frames = video_engine.generate_avatar_stream()

    async def recv(self) -> VideoFrame:
        frame = next(self._frames)
        video = VideoFrame.from_ndarray(frame, format="rgb24")
        video.pts, video.time_base = await self.next_timestamp()
        return video


@router.post("/offer")
async def offer(request: Request) -> dict[str, str]:
    """Handle WebRTC offer and return answer."""

    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    _pcs.add(pc)
    pc.addTrack(AvatarVideoTrack())
    pc.addTrack(AvatarAudioTrack())

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    logger.info("WebRTC peer connected")
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


async def close_peers() -> None:
    """Close all peer connections."""

    coros = [pc.close() for pc in list(_pcs)]
    _pcs.clear()
    for coro in coros:
        await coro


__all__ = ["router", "close_peers", "AvatarVideoTrack", "AvatarAudioTrack"]
