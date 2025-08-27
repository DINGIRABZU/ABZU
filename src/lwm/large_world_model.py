"""Minimal Large World Model converting 2D frames into a 3D scene."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Dict, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported only for type hints
    from vision.yoloe_adapter import Detection


class LargeWorldModel:
    """Construct simple 3D scenes from 2D image frames.

    The implementation is a lightweight stand‑in for heavy NeRF or Gaussian
    splatting systems. It records provided frame paths and produces a list of
    pseudo 3D points for testing and introspection.  Detection hooks allow
    upstream vision modules to attach YOLOE bounding boxes for each frame.
    """

    def __init__(self) -> None:
        self._scene: dict[str, Any] | None = None
        self._detections: Dict[int, List[Tuple[int, int, int, int]]] = {}

    def from_frames(self, frames: Iterable[Path]) -> dict[str, Any]:
        """Generate a 3D scene representation from ``frames``.

        Parameters
        ----------
        frames:
            Paths to 2D image frames.

        Returns
        -------
        dict
            A dictionary containing frame paths and placeholder 3D points.
        """
        frame_paths = [str(Path(f)) for f in frames]
        self._scene = {
            "frames": frame_paths,
            "points": [
                {"frame": path, "index": idx} for idx, path in enumerate(frame_paths)
            ],
        }
        return self._scene

    def inspect_scene(self) -> dict[str, Any]:
        """Return the last generated scene."""
        return self._scene or {}

    # ------------------------------------------------------------------
    # Detection handling
    def ingest_detections(
        self, frame_index: int, boxes: List[Tuple[int, int, int, int]]
    ) -> None:
        """Store detection ``boxes`` for ``frame_index``."""

        self._detections[frame_index] = boxes

    def get_detections(self) -> Dict[int, List[Tuple[int, int, int, int]]]:
        """Return stored detections keyed by frame index."""

        return self._detections

    def ingest_yoloe_detections(
        self, frame_index: int, detections: List["Detection"]
    ) -> None:
        """Input hook storing full YOLOE ``detections`` for ``frame_index``.

        The bounding boxes are retained in ``_detections`` and a rich detection
        payload is attached to the scene under the ``detections`` key when a
        scene exists.
        """

        self._detections[frame_index] = [d.box for d in detections]
        if self._scene is not None:
            details = [
                {
                    "label": d.label,
                    "confidence": d.confidence,
                    "box": d.box,
                }
                for d in detections
            ]
            self._scene.setdefault("detections", {})[frame_index] = details
