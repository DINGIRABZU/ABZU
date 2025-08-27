"""Minimal 2D→3D vision pipeline demonstration.

1. Generates a synthetic frame.
2. Runs YOLOE detection and forwards boxes to :class:`LargeWorldModel`.
3. Builds a simple 3D scene from the frame list.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import imageio.v2 as iio
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vision.yoloe_adapter import YOLOEAdapter
from src.lwm.large_world_model import LargeWorldModel


def generate_frame(path: Path) -> None:
    """Write a simple frame with a bright rectangle."""
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    frame[16:48, 20:44] = 255
    iio.imwrite(path, frame)


def main() -> None:
    """Run the vision wall demo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        frame_path = Path(tmpdir) / "frame.png"
        generate_frame(frame_path)

        lwm = LargeWorldModel()
        adapter = YOLOEAdapter(lwm=lwm)

        frame = iio.imread(frame_path)
        detections = adapter.detect(frame, frame_id=0)
        lwm.ingest_yoloe_detections(0, detections)

        scene = lwm.from_frames([frame_path])
        print("Scene:", scene)
        print("Detections:", lwm.get_detections())


if __name__ == "__main__":
    main()
