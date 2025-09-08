from __future__ import annotations

"""Utilities for loading LargeWorldModel rendering assets."""

__version__ = "0.1.0"

from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Tuple

import numpy as np

from ...lwm import LargeWorldModel, default_lwm
from core.video_engine import (
    AvatarTraits,
    default_render_2d_frame,
    default_render_3d_frame,
    register_render_2d,
    register_render_3d,
)

try:  # pragma: no cover - optional dependency
    import librosa  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - optional
    librosa = None  # type: ignore[assignment]


class LWMRenderer:
    """Load meshes, camera paths and lip-sync data for 3-D avatars."""

    def __init__(self, model: LargeWorldModel | None = None) -> None:
        self.model = model or default_lwm
        self.meshes: List[np.ndarray] = []
        self.camera_paths: List[Tuple[float, float, float]] = []
        self.audio_wave: np.ndarray | None = None
        self.step: int = 0

    def load_resources(
        self,
        mesh_paths: Iterable[Path],
        camera_paths: Iterable[Tuple[float, float, float]] | None = None,
        lip_sync_audio: Path | None = None,
    ) -> None:
        """Load scene assets for a configured 3-D model."""

        self.meshes = [self._load_mesh(p) for p in mesh_paths]
        if camera_paths is not None:
            self.camera_paths = list(camera_paths)
        else:
            scene = self.model.inspect_scene()
            points = scene.get("points") if isinstance(scene, dict) else None
            if points:
                self.camera_paths = [
                    (float(p.get("index", 0)), 0.0, 0.0) for p in points
                ]
        if lip_sync_audio is not None and librosa is not None:
            try:
                self.audio_wave, sr = librosa.load(
                    str(lip_sync_audio), sr=16000, mono=True
                )
                self.step = sr // 15
            except Exception:  # pragma: no cover - optional
                self.audio_wave = None
                self.step = 0

    @staticmethod
    def _load_mesh(path: Path) -> np.ndarray:
        """Read a mesh from ``path`` returning an empty array on failure."""

        try:
            return np.loadtxt(path)
        except Exception:  # pragma: no cover - defensive
            return np.empty((0, 3))


# ---------------------------------------------------------------------------
# Plug-in registration

_renderer = LWMRenderer()


def configure_renderer(
    mesh_paths: Iterable[Path],
    camera_paths: Iterable[Tuple[float, float, float]] | None = None,
    lip_sync_audio: Path | None = None,
) -> None:
    """Load resources used by the plug-in renderers."""

    _renderer.load_resources(mesh_paths, camera_paths, lip_sync_audio)


def _render_2d_frame(
    traits: AvatarTraits,
    mesh: Optional[object],
    predictor: Optional[object],
    audio_wave: Optional[np.ndarray],
    step: int,
    idx: int,
    sadtalker_frames: Optional[Iterator[np.ndarray]],
) -> tuple[np.ndarray, int]:
    if audio_wave is None and _renderer.audio_wave is not None:
        audio_wave = _renderer.audio_wave
        step = _renderer.step
    return default_render_2d_frame(
        traits, mesh, predictor, audio_wave, step, idx, sadtalker_frames
    )


def _render_3d_frame(
    traits: AvatarTraits,
    mesh: Optional[object],
    predictor: Optional[object],
    audio_wave: Optional[np.ndarray],
    step: int,
    idx: int,
    sadtalker_frames: Optional[Iterator[np.ndarray]],
    cam_iter: Optional[Iterator[Tuple[float, float, float]]],
) -> tuple[np.ndarray, int]:
    if cam_iter is None and _renderer.camera_paths:
        cam_iter = iter(_renderer.camera_paths)
    if audio_wave is None and _renderer.audio_wave is not None:
        audio_wave = _renderer.audio_wave
        step = _renderer.step
    return default_render_3d_frame(
        traits,
        mesh,
        predictor,
        audio_wave,
        step,
        idx,
        sadtalker_frames,
        cam_iter,
    )


register_render_2d(_render_2d_frame)
register_render_3d(_render_3d_frame)


__all__ = ["LWMRenderer", "configure_renderer"]
