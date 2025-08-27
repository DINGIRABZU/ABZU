from __future__ import annotations

import numpy as np

from vision.yoloe_adapter import YOLOEAdapter
from src.lwm.large_world_model import LargeWorldModel


def generate_sample() -> "np.ndarray":
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    frame[8:24, 10:22] = 255  # simple non-zero region
    return frame


def test_adapter_emits_detections_to_lwm() -> None:
    frame = generate_sample()
    lwm = LargeWorldModel()
    adapter = YOLOEAdapter(lwm=lwm)
    detections = adapter.detect(frame, frame_id=0)
    assert detections, "No detections returned"
    stored = lwm.get_detections()
    assert 0 in stored
    assert stored[0][0] == detections[0].box
