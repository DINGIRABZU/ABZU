from __future__ import annotations

"""Basic audio DSP utilities using ffmpeg and pydub."""

from pathlib import Path
from typing import Tuple
import subprocess
import tempfile

import numpy as np
import soundfile as sf

try:  # pragma: no cover - optional dependency
    from pydub import AudioSegment
except Exception:  # pragma: no cover - optional dependency
    AudioSegment = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import rave
    import torch
except Exception:  # pragma: no cover - optional dependency
    rave = None  # type: ignore
    torch = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from magenta.models.nsynth.wavenet import fastgen as nsynth_fastgen
except Exception:  # pragma: no cover - optional dependency
    nsynth_fastgen = None  # type: ignore


# ---------------------------------------------------------------------------
# ffmpeg based helpers
# ---------------------------------------------------------------------------

def _apply_ffmpeg_filter(data: np.ndarray, sr: int, filters: str) -> Tuple[np.ndarray, int]:
    """Run ``filters`` on ``data`` using ``ffmpeg``."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as inp:
        sf.write(inp.name, data, sr)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out:
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "quiet",
            "-i",
            inp.name,
            "-af",
            filters,
            out.name,
        ]
        subprocess.run(cmd, check=True)
        out_data, out_sr = sf.read(out.name, dtype=data.dtype)
    return out_data, int(out_sr)


def pitch_shift(data: np.ndarray, sr: int, semitones: float) -> Tuple[np.ndarray, int]:
    """Shift ``data`` by ``semitones`` using ``ffmpeg``."""
    factor = 2 ** (semitones / 12)
    filters = f"asetrate={int(sr * factor)},aresample={sr}"
    return _apply_ffmpeg_filter(data, sr, filters)


def time_stretch(data: np.ndarray, sr: int, rate: float) -> Tuple[np.ndarray, int]:
    """Change playback speed of ``data`` without altering pitch."""
    filters = f"atempo={rate}"
    return _apply_ffmpeg_filter(data, sr, filters)


def compress(data: np.ndarray, sr: int, threshold: float = -18.0, ratio: float = 2.0) -> Tuple[np.ndarray, int]:
    """Apply dynamic range compression using ``ffmpeg``."""
    filters = f"acompressor=threshold={threshold}:ratio={ratio}"
    return _apply_ffmpeg_filter(data, sr, filters)


# ---------------------------------------------------------------------------
# Optional RAVE support
# ---------------------------------------------------------------------------

def rave_encode(data: np.ndarray, sr: int, checkpoint: Path) -> np.ndarray:
    """Return RAVE latents for ``data`` using ``checkpoint``."""
    if rave is None or torch is None:  # pragma: no cover - optional dependency
        raise RuntimeError("rave library required")
    device = "cpu"
    model = rave.RAVE(checkpoint, device=device)
    with torch.no_grad():
        latents = model.encode(torch.from_numpy(data).unsqueeze(0))
    return latents.squeeze(0).cpu().numpy()


def rave_decode(latents: np.ndarray, sr: int, checkpoint: Path) -> Tuple[np.ndarray, int]:
    """Synthesize audio from RAVE ``latents``."""
    if rave is None or torch is None:  # pragma: no cover - optional dependency
        raise RuntimeError("rave library required")
    device = "cpu"
    model = rave.RAVE(checkpoint, device=device)
    with torch.no_grad():
        audio = model.decode(torch.from_numpy(latents).unsqueeze(0))
    return audio.squeeze(0).cpu().numpy(), sr


def rave_morph(data_a: np.ndarray, data_b: np.ndarray, sr: int, amount: float, checkpoint: Path) -> Tuple[np.ndarray, int]:
    """Interpolate between ``data_a`` and ``data_b`` via RAVE latents."""
    z_a = rave_encode(data_a, sr, checkpoint)
    z_b = rave_encode(data_b, sr, checkpoint)
    z = (1 - amount) * z_a + amount * z_b
    return rave_decode(z, sr, checkpoint)


# ---------------------------------------------------------------------------
# Optional NSynth support
# ---------------------------------------------------------------------------

def nsynth_interpolate(data_a: np.ndarray, data_b: np.ndarray, sr: int, amount: float, checkpoint: Path) -> Tuple[np.ndarray, int]:
    """Interpolate ``data_a`` and ``data_b`` using NSynth."""
    if nsynth_fastgen is None:  # pragma: no cover - optional dependency
        raise RuntimeError("nsynth library required")
    enc_a = nsynth_fastgen.encode(data_a, sr, checkpoint)
    enc_b = nsynth_fastgen.encode(data_b, sr, checkpoint)
    enc = (1 - amount) * enc_a + amount * enc_b
    audio = nsynth_fastgen.decode(enc, checkpoint)
    return audio, sr


__all__ = [
    "pitch_shift",
    "time_stretch",
    "compress",
    "rave_encode",
    "rave_decode",
    "rave_morph",
    "nsynth_interpolate",
]

