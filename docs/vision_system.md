# Vision System

The vision module provides real‑time object detection using a YOLOE adapter. It
forwards bounding boxes to the `LargeWorldModel` for downstream processing.

## Usage

```python
from pathlib import Path
import numpy as np
from vision.yoloe_adapter import YOLOEAdapter
from src.lwm.large_world_model import LargeWorldModel

# Load model and connect to LargeWorldModel
lwm = LargeWorldModel()
adapter = YOLOEAdapter(model_path=Path("yoloe.pt"), lwm=lwm)

# Run detection on a frame
frame = np.load("tests/vision/data/sample_frame.npy")
adapter.detect(frame, frame_id=0)
print(lwm.get_detections())
```

Provide a path to YOLOE weights when available. The adapter falls back to a
simple bounding box heuristic if the model cannot be loaded.
