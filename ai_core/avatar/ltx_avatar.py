"""Lightweight wrapper for an imaginary LTX distilled avatar model.

The implementation purposely avoids external dependencies.  The goal is to
provide a tiny, synchronous interface that yields ``numpy`` frames at a steady
frame rate.  The underlying ``LTXDistilledModel`` is a minimal stub that simply
creates greyscale images whose intensity encodes the frame index.  The behaviour
is sufficient for unit tests and documentation examples and mirrors the API a
real model might expose.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator, List

import numpy as np


class LTXDistilledModel:
    """Trivial stand in for the real LTX distilled model.

    ``render`` generates ``frame_count`` square RGB frames where each frame is a
    solid colour.  The pixel value cycles between 0 and 254 and therefore the
    frames are deterministic and lightweight.
    """

    def render(self, prompt: str, frame_count: int) -> List[np.ndarray]:
        frames: List[np.ndarray] = []
        for i in range(frame_count):
            value = i % 255
            frame = np.full((64, 64, 3), value, dtype=np.uint8)
            frames.append(frame)
        return frames


@dataclass
class LTXAvatar:
    """Generate avatar frames at a fixed frame rate using ``LTXDistilledModel``."""

    model: LTXDistilledModel | None = None
    fps: int = 30

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        if self.model is None:
            self.model = LTXDistilledModel()

    def stream(self, prompt: str, seconds: float = 1.0) -> Iterator[np.ndarray]:
        """Yield frames for ``seconds`` seconds at the configured frame rate."""

        frame_count = int(self.fps * seconds)
        frames = self.model.render(prompt, frame_count)
        interval = 1.0 / self.fps if self.fps > 0 else 0.0
        for frame in frames:
            if interval:
                time.sleep(interval)
            yield frame


__all__ = ["LTXAvatar", "LTXDistilledModel"]
