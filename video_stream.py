"""Provide WebRTC streaming for avatar audio and video.

This module exposes FastAPI routes and stream tracks to deliver avatar frames
and optional audio to connected clients.
"""

from __future__ import annotations

import asyncio
import fractions
import logging
import time
from pathlib import Path
from typing import Optional, Set

import numpy as np

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
    from aiortc.mediastreams import AUDIO_PTIME, AudioStreamTrack, MediaStreamError
except Exception:  # pragma: no cover - optional dependency
    RTCPeerConnection = RTCSessionDescription = VideoStreamTrack = None  # type: ignore
    AudioStreamTrack = MediaStreamError = None  # type: ignore
    AUDIO_PTIME = 0.02

try:  # pragma: no cover - optional dependency
    from av import VideoFrame
    from av.audio.frame import AudioFrame
except Exception:  # pragma: no cover - optional dependency
    VideoFrame = AudioFrame = None  # type: ignore

from fastapi import APIRouter, HTTPException, Request

from core import avatar_expression_engine, video_engine
from src.media.video.base import VideoProcessor

logger = logging.getLogger(__name__)

_pcs: Set[RTCPeerConnection] = set()  # type: ignore[assignment]
_active_track: AvatarVideoTrack | None = None  # type: ignore  # defined later


class AvatarAudioTrack(AudioStreamTrack):
    """Audio track streaming a WAV file."""

    def __init__(self, audio_path: Optional[Path] = None) -> None:
        """Initialize track, optionally loading audio from ``audio_path``."""
        super().__init__()
        if audio_path is not None:
            if sf is None:
                raise RuntimeError("soundfile library not installed")
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
        """Yield the next chunk of audio as an ``AudioFrame``."""
        if self.readyState != "live":
            raise MediaStreamError

        if self._start is None:
            self._start = time.time()
            self._timestamp = 0
        else:
            self._timestamp += self._samples
            wait = self._start + (self._timestamp / self._sr) - time.time()
            await asyncio.sleep(max(0, wait))

        end = self._index + self._samples
        chunk = self._data[self._index : end]  # noqa: E203
        self._index = end
        if len(chunk) < self._samples:
            chunk = np.pad(
                chunk,
                (0, self._samples - len(chunk)),
                constant_values=0,
            )

        frame = AudioFrame.from_ndarray(
            chunk.reshape(1, -1), format="s16", layout="mono"
        )
        frame.pts = self._timestamp
        frame.sample_rate = self._sr
        frame.time_base = fractions.Fraction(1, self._sr)
        return frame


class AvatarVideoTrack(VideoStreamTrack):
    """Video track producing frames from ``avatar_expression_engine``."""

    def __init__(
        self,
        audio_path: Optional[Path] = None,
        cues: Optional[asyncio.Queue[str]] = None,
    ) -> None:
        """Initialize the track with optional audio path and style cues."""
        super().__init__()
        if audio_path is not None:
            self.update_audio(audio_path)
        else:
            self._frames = video_engine.generate_avatar_stream()
        self._cues = cues
        self._style: str | None = None
        global _active_track
        _active_track = self

    def update_audio(self, audio_path: Path) -> None:
        """Replace the frame generator with audio-driven stream."""
        self._frames = avatar_expression_engine.stream_avatar_audio(audio_path)

    def _cue_colour(self, text: str) -> np.ndarray:
        value = abs(hash(text)) & 0xFFFFFF
        return np.array(
            [(value >> 16) & 255, (value >> 8) & 255, value & 255],
            dtype=np.uint8,
        )

    def _apply_cue(self, frame: np.ndarray) -> np.ndarray:
        if not self._style:
            return frame
        result = frame.copy()
        color = self._cue_colour(self._style)
        h, w, _ = result.shape
        result[:10, :10] = color
        result[h - 10 :, w - 10 :] = color  # noqa: E203
        return result

    async def recv(self) -> VideoFrame:
        """Receive the next video frame from the generator."""
        if self._cues is not None:
            try:
                while True:
                    self._style = self._cues.get_nowait()
            except asyncio.QueueEmpty:
                pass
        frame = next(self._frames)
        frame = self._apply_cue(frame)
        video = VideoFrame.from_ndarray(frame, format="rgb24")
        video.pts, video.time_base = await self.next_timestamp()
        return video


class WebRTCStreamProcessor(VideoProcessor):
    """Processor handling WebRTC offers and avatar audio updates."""

    def __init__(self) -> None:
        """Create a processor and register FastAPI routes."""
        self.router = APIRouter()
        self.router.post("/offer")(self.offer)
        self.router.post("/avatar-audio")(self.avatar_audio)

    async def process(self, request: Request) -> dict[str, str]:
        """Process a generic request by delegating to :meth:`offer`."""
        return await self.offer(request)

    async def offer(self, request: Request) -> dict[str, str]:
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

    async def avatar_audio(self, request: Request) -> dict[str, str]:
        """Update the active ``AvatarVideoTrack`` with ``audio_path``."""
        data = await request.json()
        path = Path(data["path"])
        if _active_track is None:
            raise HTTPException(status_code=404, detail="no active track")
        _active_track.update_audio(path)
        logger.info("Updated avatar audio: %s", path)
        return {"status": "ok"}

    async def close_peers(self) -> None:
        """Close all peer connections."""
        coros = [pc.close() for pc in list(_pcs)]
        _pcs.clear()
        for coro in coros:
            await coro
        global _active_track
        _active_track = None


processor = WebRTCStreamProcessor()
router = processor.router
offer = processor.offer
avatar_audio = processor.avatar_audio
close_peers = processor.close_peers

__all__ = ["router", "close_peers", "AvatarVideoTrack", "AvatarAudioTrack"]
