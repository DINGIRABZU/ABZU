from __future__ import annotations

"""Utility functions to log session audio and video."""

from pathlib import Path
from datetime import datetime
import logging
import shutil
from typing import Iterable

try:  # pragma: no cover - optional dependency
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import imageio.v2 as imageio  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    imageio = None  # type: ignore

logger = logging.getLogger(__name__)

AUDIO_DIR = Path("logs/audio")
VIDEO_DIR = Path("logs/video")


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def log_audio(path: str | Path) -> Path:
    """Copy ``path`` into :data:`AUDIO_DIR` with a timestamped name."""
    src = Path(path)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    dest = AUDIO_DIR / f"{_timestamp()}{src.suffix}"
    shutil.copy2(src, dest)
    logger.info("logged audio to %s", dest)
    return dest


def log_video(frames: Iterable[np.ndarray]) -> Path:
    """Save ``frames`` to :data:`VIDEO_DIR` and return the output path."""
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    if imageio is not None:
        dest = VIDEO_DIR / f"{ts}.mp4"
        writer = imageio.get_writer(dest, fps=15)
        for frame in frames:
            writer.append_data(frame)
        writer.close()
    elif np is not None and hasattr(np, "stack") and hasattr(np, "savez_compressed"):
        dest = VIDEO_DIR / f"{ts}.npz"
        arr = np.stack(list(frames))
        np.savez_compressed(dest, frames=arr)
    else:
        dest = VIDEO_DIR / f"{ts}.bin"
        import pickle

        with open(dest, "wb") as fh:
            pickle.dump(list(frames), fh)
    logger.info("logged video to %s", dest)
    return dest


__all__ = ["log_audio", "log_video"]
