"""Minimal audio segment abstraction with optional NumPy backend.

This module exposes :class:`AudioSegment` which resolves to the pydub class
when available.  When pydub or the required ``ffmpeg`` binary is missing the
module falls back to a small NumPy implementation offering a subset of the
pydub API used across the project.  The NumPy backend relies on ``soundfile``
for I/O and performs simple operations such as overlay, gain, panning and
fades directly on arrays.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from core.utils.optional_deps import lazy_import

logger = logging.getLogger(__name__)


def has_ffmpeg() -> bool:
    """Return ``True`` if the ``ffmpeg`` binary is available and executable."""

    path = shutil.which("ffmpeg")
    if not path:
        return False
    try:  # pragma: no cover - runtime environment check
        subprocess.run(
            [path, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception:
        return False
    return True


_backend_env = os.environ.get("AUDIO_BACKEND")
_backend = (_backend_env or "pydub").lower()
_ffmpeg_available = has_ffmpeg()

if _backend not in {"numpy", "pydub"}:
    if _backend == "auto":
        _backend = "pydub"
    else:  # pragma: no cover - defensive branch
        logger.warning(
            "Unknown AUDIO_BACKEND '%s'; defaulting to NumPy backend", _backend
        )
        _backend = "numpy"

if _backend_env is None:
    # Promote the preferred backend to the environment for downstream tools.
    if _backend == "pydub" and not _ffmpeg_available:
        logger.error("FFmpeg binary missing; falling back to NumPy audio backend")
        _backend = "numpy"
    os.environ["AUDIO_BACKEND"] = _backend

if _backend != "numpy":
    pydub = lazy_import("pydub")
    _PydubSegment = getattr(pydub, "AudioSegment", None)
    _pydub_errors: list[str] = []

    if getattr(pydub, "__stub__", False):
        _pydub_errors.append("pydub is not installed")
    if not _ffmpeg_available:
        _pydub_errors.append("ffmpeg binary not found")
    if _PydubSegment is None:
        _pydub_errors.append("pydub.AudioSegment not available")

    if _pydub_errors:
        logger.error(
            "Cannot activate pydub audio backend (%s); using NumPy fallback",
            "; ".join(_pydub_errors),
        )
        _PydubSegment = None  # type: ignore[assignment]
else:  # pragma: no cover - respect backend choice
    _PydubSegment = None  # type: ignore[assignment]

sf = lazy_import("soundfile")
if getattr(sf, "__stub__", False):
    sf = None  # type: ignore


@dataclass
class NpAudioSegment:
    """Lightweight replacement for :class:`pydub.AudioSegment`."""

    data: np.ndarray
    frame_rate: int

    @classmethod
    def from_file(cls, path: Path) -> "NpAudioSegment":
        if sf is None:  # pragma: no cover - optional dependency
            raise RuntimeError("soundfile library required")
        data, sr = sf.read(path, always_2d=True, dtype="float32")
        return cls(data, int(sr))

    # ------------------------------------------------------------------
    # Basic exporters
    # ------------------------------------------------------------------
    def export(self, path: Path, format: str = "wav") -> None:
        if sf is None:  # pragma: no cover - optional dependency
            raise RuntimeError("soundfile library required")
        sf.write(path, self.data, self.frame_rate)

    # ------------------------------------------------------------------
    # Simple edits
    # ------------------------------------------------------------------
    def apply_gain(self, db: float) -> "NpAudioSegment":
        factor = 10 ** (db / 20)
        return NpAudioSegment(self.data * factor, self.frame_rate)

    def pan(self, value: float) -> "NpAudioSegment":
        value = float(max(-1.0, min(1.0, value)))
        if self.data.shape[1] == 1:
            left = self.data[:, 0] * (1 - value) / 2
            right = self.data[:, 0] * (1 + value) / 2
            data = np.column_stack([left, right])
        else:
            left = self.data[:, 0] * (1 - value) / 2
            right = self.data[:, 1] * (1 + value) / 2
            data = np.column_stack([left, right])
        return NpAudioSegment(data.astype(self.data.dtype), self.frame_rate)

    def overlay(self, other: "NpAudioSegment", position: int = 0) -> "NpAudioSegment":
        pos = int(position * self.frame_rate / 1000)
        base = self.data.copy()
        end = pos + other.data.shape[0]
        if end > base.shape[0]:
            pad = np.zeros((end - base.shape[0], base.shape[1]), dtype=base.dtype)
            base = np.vstack([base, pad])
        base[pos:end] += other.data
        return NpAudioSegment(base, self.frame_rate)

    def reverse(self) -> "NpAudioSegment":
        return NpAudioSegment(self.data[::-1], self.frame_rate)

    def fade_in(self, duration_ms: int) -> "NpAudioSegment":
        samples = int(duration_ms * self.frame_rate / 1000)
        samples = min(samples, self.data.shape[0])
        ramp = np.linspace(0.0, 1.0, samples, endpoint=True)
        data = self.data.copy()
        data[:samples] *= ramp[:, None]
        return NpAudioSegment(data, self.frame_rate)

    def fade_out(self, duration_ms: int) -> "NpAudioSegment":
        samples = int(duration_ms * self.frame_rate / 1000)
        samples = min(samples, self.data.shape[0])
        ramp = np.linspace(1.0, 0.0, samples, endpoint=True)
        data = self.data.copy()
        data[-samples:] *= ramp[:, None]
        return NpAudioSegment(data, self.frame_rate)

    def __getitem__(self, item: slice) -> "NpAudioSegment":
        if not isinstance(item, slice):  # pragma: no cover - defensive
            raise TypeError("slice expected")
        start_ms = 0 if item.start is None else int(item.start)
        end_ms = (
            self.data.shape[0] * 1000 // self.frame_rate
            if item.stop is None
            else int(item.stop)
        )
        start = int(start_ms * self.frame_rate / 1000)
        end = int(end_ms * self.frame_rate / 1000)
        return NpAudioSegment(self.data[start:end], self.frame_rate)


# Resolve backend -------------------------------------------------------------

_use_pydub = _backend != "numpy" and _PydubSegment is not None

if _use_pydub:
    AudioSegment = _PydubSegment  # type: ignore
else:
    AudioSegment = NpAudioSegment

__all__ = ["AudioSegment", "NpAudioSegment", "has_ffmpeg"]
