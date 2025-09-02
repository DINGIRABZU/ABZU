"""YOLOE wrapper emitting detections to the LargeWorldModel."""

from __future__ import annotations

__version__ = "0.1.0"

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

try:  # pragma: no cover - optional dependency
    from ultralytics import YOLO  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    YOLO = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single detection result."""

    label: str
    confidence: float
    box: Tuple[int, int, int, int]


class YOLOEAdapter:
    """Run YOLOE detection and forward boxes to ``LargeWorldModel``."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        lwm: "LargeWorldModel" | None = None,
    ) -> None:
        self.lwm = lwm
        self.model = None
        if YOLO is not None:
            weights = str(model_path) if model_path else "yoloe.pt"
            try:  # pragma: no cover - optional dependency
                self.model = YOLO(weights)
            except Exception as exc:  # pragma: no cover - optional dependency
                logger.warning("Could not load YOLOE model: %s", exc)

    def detect(
        self, frame: "np.ndarray", frame_id: int | None = None
    ) -> List[Detection]:
        """Return detections for ``frame`` and emit boxes to ``LargeWorldModel``."""

        boxes: List[Detection] = []
        if self.model is not None:  # pragma: no branch - requires model
            results = self.model(frame)
            names = getattr(
                self.model,
                "names",
                getattr(self.model, "model", None) and self.model.model.names,
            )
            for r in results:
                for b in r.boxes:
                    cls_name = names[int(b.cls)] if names else str(int(b.cls))
                    conf = float(b.conf)
                    x1, y1, x2, y2 = b.xyxy[0].tolist()
                    boxes.append(
                        Detection(cls_name, conf, (int(x1), int(y1), int(x2), int(y2)))
                    )
        elif np is not None:
            ys, xs = np.where(frame.sum(axis=-1) > 0)
            if ys.size and xs.size:
                x1, x2 = xs.min(), xs.max()
                y1, y2 = ys.min(), ys.max()
                boxes.append(Detection("object", 1.0, (x1, y1, x2, y2)))
        if frame_id is not None and self.lwm is not None:
            self.lwm.ingest_detections(frame_id, [d.box for d in boxes])
        return boxes

    def process_stream(
        self, frames: Iterable["np.ndarray"]
    ) -> Iterable[List[Detection]]:
        """Yield detections for each frame in ``frames``."""

        for idx, frame in enumerate(frames):
            yield self.detect(frame, frame_id=idx)


__all__ = ["YOLOEAdapter", "Detection"]
