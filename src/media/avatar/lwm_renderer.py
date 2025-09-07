from __future__ import annotations

"""Utilities for loading LargeWorldModel rendering assets."""

__version__ = "0.1.0"

from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np

from ...lwm import LargeWorldModel, default_lwm

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


__all__ = ["LWMRenderer"]
