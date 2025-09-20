"""Arrange and export audio stems produced by :mod:`vocal_isolation`.

Groups instrument layers and writes combined stems for downstream
processing.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from time import perf_counter
from typing import Dict, Iterable, List, Sequence

try:  # pragma: no cover - optional dependency
    from audio.segment import AudioSegment
except Exception:  # pragma: no cover - optional dependency
    AudioSegment = None  # type: ignore

from src.audio.telemetry import telemetry


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def layer_stems(
    stems: Dict[str, Path],
    pans: Iterable[float] | None = None,
    volumes: Iterable[float] | None = None,
) -> AudioSegment:
    """Return a stereo mix by overlaying ``stems`` with optional ``pans``
    and ``volumes``.

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
    start = perf_counter()
    backend = "pydub" if AudioSegment is not None else "unavailable"
    stem_items = list(stems.items())
    if AudioSegment is None:  # pragma: no cover - optional dependency
        telemetry.emit(
            "modulation.layer_stems",
            backend=backend,
            status="failure",
            reason="audio_segment_unavailable",
            stem_count=len(stem_items),
            duration_s=perf_counter() - start,
        )
        raise RuntimeError("pydub library required")

    segs: List[AudioSegment] = []
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

    telemetry.emit(
        "modulation.layer_stems",
        backend=backend,
        status="success",
        stem_count=len(stem_items),
        duration_s=perf_counter() - start,
    )
    return mix


def slice_loop(segment: AudioSegment, start: float, duration: float) -> AudioSegment:
    """Return ``segment`` section starting at ``start`` seconds of ``duration``."""
    start_ms = int(start * 1000)
    end_ms = int((start + duration) * 1000)
    return segment[start_ms:end_ms]


def apply_fades(
    segment: AudioSegment, fade_in_ms: int = 0, fade_out_ms: int = 0
) -> AudioSegment:
    """Apply fades to ``segment`` and return a new :class:`AudioSegment`."""
    if fade_in_ms:
        segment = segment.fade_in(fade_in_ms)
    if fade_out_ms:
        segment = segment.fade_out(fade_out_ms)
    return segment


def export_mix(segment: AudioSegment, path: Path, format: str = "wav") -> None:
    """Export ``segment`` to ``path`` in ``format``."""
    start = perf_counter()
    backend = "pydub" if hasattr(segment, "export") else "unknown"
    try:
        segment.export(path, format=format)
    except Exception as exc:
        telemetry.emit(
            "modulation.export_mix",
            backend=backend,
            status="failure",
            error=str(exc),
            path=path,
            format=format,
            duration_s=perf_counter() - start,
        )
        raise
    telemetry.emit(
        "modulation.export_mix",
        backend=backend,
        status="success",
        path=path,
        format=format,
        duration_s=perf_counter() - start,
    )


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
    overall_start = perf_counter()
    export_mix(segment, audio_path)
    if session_format is None:
        telemetry.emit(
            "modulation.export_session",
            status="audio_only",
            session_format=session_format,
            audio_path=audio_path,
            duration_s=perf_counter() - overall_start,
        )
        return None

    try:
        session_start = perf_counter()
        if session_format == "ardour":
            path = write_ardour_session(audio_path, audio_path.with_suffix(".ardour"))
        elif session_format == "carla":
            path = write_carla_project(audio_path, audio_path.with_suffix(".carxs"))
        else:
            telemetry.emit(
                "modulation.export_session",
                status="skipped",
                session_format=session_format,
                audio_path=audio_path,
                duration_s=perf_counter() - session_start,
                reason="unsupported_format",
            )
            return None
        telemetry.emit(
            "modulation.export_session",
            status="success",
            session_format=session_format,
            audio_path=audio_path,
            session_path=path,
            duration_s=perf_counter() - session_start,
        )
        return path
    except DAWUnavailableError as exc:
        telemetry.emit(
            "modulation.export_session",
            status="fallback",
            session_format=session_format,
            audio_path=audio_path,
            duration_s=perf_counter() - overall_start,
            available=exc.available,
            remediation=exc.remediation,
        )
        logger.warning(
            "Skipping %s session export because the DAW tooling is unavailable: %s",
            session_format,
            exc,
        )
        logger.debug("DAW availability snapshot: %s", exc.available)
    except Exception as exc:
        telemetry.emit(
            "modulation.export_session",
            status="failure",
            session_format=session_format,
            audio_path=audio_path,
            duration_s=perf_counter() - overall_start,
            error=str(exc),
        )
        raise
    return None


# ---------------------------------------------------------------------------
# Optional session file helpers
# ---------------------------------------------------------------------------


logger = logging.getLogger(__name__)


def _tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def _resolve_tool(candidates: Sequence[str]) -> str | None:
    for name in candidates:
        if _tool_available(name):
            return name
    return None


def _format_tool_list(candidates: Sequence[str]) -> str:
    if not candidates:
        return ""
    if len(candidates) == 1:
        return candidates[0]
    return ", ".join(candidates[:-1]) + f" or {candidates[-1]}"


class DAWUnavailableError(RuntimeError):
    """Raised when an expected digital audio workstation is missing."""

    def __init__(
        self,
        tools: Sequence[str],
        remediation: str,
        available: Dict[str, bool] | None = None,
    ) -> None:
        self.tools = tuple(dict.fromkeys(tools))
        self.remediation = remediation
        self.available = available or {}
        message = (
            "Missing DAW tool(s) on PATH: "
            f"{_format_tool_list(self.tools)}. {self.remediation}"
        )
        super().__init__(message)


ARDOUR_CANDIDATES = ("ardour7", "ardour6", "ardour")
CARLA_CANDIDATES = ("carla",)


def write_ardour_session(audio_path: Path, out_path: Path) -> Path:
    """Write a minimal Ardour session referencing ``audio_path``."""
    if _resolve_tool(ARDOUR_CANDIDATES) is None:
        raise DAWUnavailableError(
            ARDOUR_CANDIDATES,
            (
                "Install Ardour and ensure its binary is on PATH or disable "
                "Ardour session export."
            ),
        )
    xml = f'<Session><Sources><Source name="{audio_path}"/></Sources></Session>'
    out_path.write_text(xml)
    return out_path


def write_carla_project(audio_path: Path, out_path: Path) -> Path:
    """Write a simple Carla rack session referencing ``audio_path``."""
    if _resolve_tool(CARLA_CANDIDATES) is None:
        raise DAWUnavailableError(
            CARLA_CANDIDATES,
            (
                "Install Carla or remove Carla session export from the "
                "rehearsal recipe."
            ),
        )
    xml = (
        "<?xml version='1.0'?><CarlaPatchbay><File name=\""
        f"{audio_path}"
        '"/></CarlaPatchbay>'
    )
    out_path.write_text(xml)
    return out_path


def check_daw_availability(
    require_ardour: bool = True,
    require_carla: bool = True,
    log: logging.Logger | None = None,
) -> Dict[str, bool]:
    """Return a map of DAW availability and raise when required tools are missing."""

    available = {
        "ardour": _resolve_tool(ARDOUR_CANDIDATES) is not None,
        "carla": _resolve_tool(CARLA_CANDIDATES) is not None,
    }
    required_missing: list[str] = []
    if require_ardour and not available["ardour"]:
        required_missing.extend(ARDOUR_CANDIDATES)
    if require_carla and not available["carla"]:
        required_missing.extend(CARLA_CANDIDATES)

    target_logger = log if log is not None else logger
    target_logger.debug("DAW preflight availability: %s", available)

    if required_missing:
        remediation = (
            "Install the missing DAW executables or disable session export for them."
        )
        error = DAWUnavailableError(required_missing, remediation, available)
        target_logger.error("%s", error)
        raise error

    return available


__all__ = [
    "layer_stems",
    "slice_loop",
    "apply_fades",
    "export_mix",
    "export_session",
    "write_ardour_session",
    "write_carla_project",
    "check_daw_availability",
    "DAWUnavailableError",
]
