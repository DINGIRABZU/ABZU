"""Runtime stub for :mod:`simpleaudio` used during Stage B rehearsals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["play_buffer", "__version__", "__ABZU_FALLBACK__"]

__version__ = "0.0.0-stub"
__ABZU_FALLBACK__ = True


@dataclass
class _Playback:
    channels: int
    bytes_per_sample: int
    sample_rate: int

    def wait_done(self) -> None:  # pragma: no cover - trivial noop
        return None


def play_buffer(
    _audio: Any,
    channels: int,
    bytes_per_sample: int,
    sample_rate: int,
) -> _Playback:
    """Return a dummy playback object that no-ops when waited upon."""

    return _Playback(
        channels=channels,
        bytes_per_sample=bytes_per_sample,
        sample_rate=sample_rate,
    )
