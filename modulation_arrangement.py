from __future__ import annotations

"""Arrange and export audio stems produced by :mod:`vocal_isolation`."""

from pathlib import Path
from typing import Dict, Iterable, List
import shutil

try:  # pragma: no cover - optional dependency
    from pydub import AudioSegment
except Exception:  # pragma: no cover - optional dependency
    AudioSegment = None  # type: ignore


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def layer_stems(
    stems: Dict[str, Path],
    pans: Iterable[float] | None = None,
    volumes: Iterable[float] | None = None,
) -> AudioSegment:
    """Return a stereo mix by overlaying ``stems`` with optional ``pans`` and ``volumes``.

    Parameters
    ----------
    stems:
        Mapping of stem name to audio file path.
    pans:
        Iterable of pan positions between ``-1`` (left) and ``1`` (right). When
        ``None`` the function spreads the stems evenly across the stereo field.
    volumes:
        Iterable of gain offsets in decibels applied to each stem. ``None``
        leaves the original volume unchanged.
    """
    if AudioSegment is None:  # pragma: no cover - optional dependency
        raise RuntimeError("pydub library required")

    segs: List[AudioSegment] = []
    stem_items = list(stems.items())
    total = len(stem_items)
    pan_list = list(pans) if pans is not None else None
    vol_list = list(volumes) if volumes is not None else None
    for idx, (_name, path) in enumerate(stem_items):
        seg = AudioSegment.from_file(path)
        if vol_list is not None:
            seg = seg.apply_gain(vol_list[idx % len(vol_list)])
        if pan_list is not None:
            pan = pan_list[idx % len(pan_list)]
        else:
            pan = (idx - (total - 1) / 2) / (total / 2) if total > 1 else 0
        segs.append(seg.pan(pan))

    mix = segs[0]
    for seg in segs[1:]:
        mix = mix.overlay(seg)
    return mix


def slice_loop(segment: AudioSegment, start: float, duration: float) -> AudioSegment:
    """Return ``segment`` section starting at ``start`` seconds of ``duration``."""
    start_ms = int(start * 1000)
    end_ms = int((start + duration) * 1000)
    return segment[start_ms:end_ms]


def apply_fades(segment: AudioSegment, fade_in_ms: int = 0, fade_out_ms: int = 0) -> AudioSegment:
    """Apply fades to ``segment`` and return a new :class:`AudioSegment`."""
    if fade_in_ms:
        segment = segment.fade_in(fade_in_ms)
    if fade_out_ms:
        segment = segment.fade_out(fade_out_ms)
    return segment


def export_mix(segment: AudioSegment, path: Path, format: str = "wav") -> None:
    """Export ``segment`` to ``path`` in ``format``."""
    segment.export(path, format=format)


def export_session(
    segment: AudioSegment,
    audio_path: Path,
    session_format: str | None = None,
) -> Path | None:
    """Export ``segment`` and optionally create a session file.

    Parameters
    ----------
    segment:
        Audio data to export.
    audio_path:
        Destination of the rendered audio file.
    session_format:
        ``"ardour"`` or ``"carla"`` to create an accompanying session file.
    """
    export_mix(segment, audio_path)
    if session_format == "ardour":
        return write_ardour_session(audio_path, audio_path.with_suffix(".ardour"))
    if session_format == "carla":
        return write_carla_project(audio_path, audio_path.with_suffix(".carxs"))
    return None


# ---------------------------------------------------------------------------
# Optional session file helpers
# ---------------------------------------------------------------------------

def _tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def write_ardour_session(audio_path: Path, out_path: Path) -> Path:
    """Write a minimal Ardour session referencing ``audio_path``."""
    if not (_tool_available("ardour6") or _tool_available("ardour7") or _tool_available("ardour")):
        raise RuntimeError("Ardour not installed")
    xml = f"<Session><Sources><Source name=\"{audio_path}\"/></Sources></Session>"
    out_path.write_text(xml)
    return out_path


def write_carla_project(audio_path: Path, out_path: Path) -> Path:
    """Write a simple Carla rack session referencing ``audio_path``."""
    if not _tool_available("carla"):
        raise RuntimeError("Carla not installed")
    xml = f"<?xml version='1.0'?><CarlaPatchbay><File name=\"{audio_path}\"/></CarlaPatchbay>"
    out_path.write_text(xml)
    return out_path


__all__ = [
    "layer_stems",
    "slice_loop",
    "apply_fades",
    "export_mix",
    "export_session",
    "write_ardour_session",
    "write_carla_project",
]
