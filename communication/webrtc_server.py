"""WebRTC signaling helpers and media tracks.

This module exposes a minimal MediaSoup signalling server as well as utility
tracks for streaming avatar video and audio.  The media tracks reference the
``start_stream`` endpoints from :mod:`core.video_engine` and
``core.avatar_expression_engine``, allowing external clients to receive the
avatar's rendered output over WebRTC.
"""

from __future__ import annotations

import asyncio
import fractions
import importlib
import logging
import time
from pathlib import Path
from typing import Any, Iterator, Optional, cast

import numpy as np

try:  # pragma: no cover - optional dependency
    import mediasoup  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    mediasoup = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from aiortc import VideoStreamTrack
    from aiortc.mediastreams import AUDIO_PTIME, AudioStreamTrack, MediaStreamError
except Exception:  # pragma: no cover - optional dependency
    VideoStreamTrack = cast(Any, object)
    AudioStreamTrack = cast(Any, object)
    MediaStreamError = cast(Any, RuntimeError)
    AUDIO_PTIME = 0.02

try:  # pragma: no cover - optional dependency
    _VideoFrame = getattr(importlib.import_module("av"), "VideoFrame")
    _AudioFrame = getattr(importlib.import_module("av.audio.frame"), "AudioFrame")
except Exception:  # pragma: no cover - optional dependency

    class _VideoFrameStub:
        @staticmethod
        def from_ndarray(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("av library not installed")

    class _AudioFrameStub:
        @staticmethod
        def from_ndarray(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("av library not installed")

    _VideoFrame = _VideoFrameStub
    _AudioFrame = _AudioFrameStub

VideoFrame = _VideoFrame
AudioFrame = _AudioFrame

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = cast(Any, None)

from core import video_engine

logger = logging.getLogger(__name__)


class AvatarAudioTrack(AudioStreamTrack):  # type: ignore[misc]
    """Audio track streaming WAV data or silence.

    Parameters
    ----------
    audio_path:
        Optional path to a WAV file.  If omitted, the track generates silent
        audio at 8 kHz.  When provided, the file is streamed using the
        ``soundfile`` package.
    """

    def __init__(self, audio_path: Optional[Path] = None) -> None:
        """Create a track optionally initialised with ``audio_path``."""
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

    async def recv(self) -> Any:
        """Yield the next chunk of audio as an ``AudioFrame``."""
        if self.readyState != "live":  # pragma: no cover - defensive
            raise MediaStreamError

        if self._start is None:
            self._start = time.time()
            self._timestamp = 0
        else:
            self._timestamp += self._samples
            wait = self._start + (self._timestamp / self._sr) - time.time()
            await asyncio.sleep(max(0, wait))

        end = self._index + self._samples
        chunk = self._data[self._index : end]
        self._index = end
        if len(chunk) < self._samples:
            chunk = np.pad(chunk, (0, self._samples - len(chunk)), constant_values=0)

        frame = AudioFrame.from_ndarray(
            chunk.reshape(1, -1), format="s16", layout="mono"
        )
        frame.pts = self._timestamp
        frame.sample_rate = self._sr
        frame.time_base = fractions.Fraction(1, self._sr)
        return frame


class AvatarVideoTrack(VideoStreamTrack):  # type: ignore[misc]
    """Video track producing frames from ``video_engine.start_stream``."""

    def __init__(self) -> None:
        """Initialise the track using ``video_engine.start_stream``."""
        super().__init__()
        self._frames: Iterator[np.ndarray] = video_engine.start_stream()

    async def recv(self) -> Any:
        """Return the next video frame from the generator."""
        frame = next(self._frames)
        video = VideoFrame.from_ndarray(frame, format="rgb24")
        video.pts, video.time_base = await self.next_timestamp()
        return video


class WebRTCServer:
    """Minimal MediaSoup-based SFU server with helper tracks."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Prepare server state for later startup."""
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


__all__ = ["WebRTCServer", "AvatarVideoTrack", "AvatarAudioTrack"]
