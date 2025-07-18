from __future__ import annotations

"""Screen capture and GUI detection utilities."""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

try:  # pragma: no cover - optional dependency
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cv2 = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from ultralytics import YOLO  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    YOLO = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pyautogui = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ObservedElement:
    """Single detected UI element."""

    label: str
    confidence: float
    box: Tuple[int, int, int, int]
    text: Optional[str] = None


def capture_screen(
    region: Tuple[int, int, int, int] | None = None,
) -> Optional["np.ndarray"]:
    """Return a screenshot as an RGB array."""
    if pyautogui is None or cv2 is None or np is None:
        logger.warning("Screen capture requires pyautogui and opencv-python")
        return None
    image = pyautogui.screenshot(region=region)
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return frame


def screen_stream(
    fps: int = 1,
    region: Tuple[int, int, int, int] | None = None,
) -> Iterable["np.ndarray"]:
    """Yield successive screen captures at ``fps`` frames per second."""
    delay = 1.0 / max(fps, 1)
    while True:
        frame = capture_screen(region)
        if frame is None:
            break
        yield frame
        time.sleep(delay)


def detect_gui_elements(
    image: "np.ndarray", model_path: str | Path | None = None
) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
    """Detect GUI elements in ``image`` using YOLOv8."""
    if YOLO is None or cv2 is None:
        logger.warning("YOLOv8 or OpenCV not available")
        return []
    model = YOLO(str(model_path) if model_path else "yolov8n.pt")
    results = model(image)
    detections: List[Tuple[str, float, Tuple[int, int, int, int]]] = []
    names = getattr(model, "names", getattr(model, "model", None) and model.model.names)
    for r in results:
        for box in r.boxes:
            cls_name = names[int(box.cls)] if names else str(int(box.cls))
            conf = float(box.conf)
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append((cls_name, conf, (int(x1), int(y1), int(x2), int(y2))))
    return detections


def extract_text(image: "np.ndarray") -> str:
    """Return text found in ``image`` using Tesseract OCR."""
    if pytesseract is None:
        logger.warning("pytesseract not installed")
        return ""
    return pytesseract.image_to_string(image)


def analyze_frame(
    frame: "np.ndarray",
    model_path: str | Path | None = None,
    ocr_labels: Sequence[str] | None = None,
) -> List[ObservedElement]:
    """Return detected elements and optional OCR from ``frame``."""
    elements = []
    for label, conf, box in detect_gui_elements(frame, model_path):
        text = None
        if ocr_labels and label in ocr_labels:
            x1, y1, x2, y2 = box
            region = frame[y1:y2, x1:x2]
            text = extract_text(region)
        elements.append(ObservedElement(label, conf, box, text))
    return elements


def observe_screen(
    fps: int = 1,
    model_path: str | Path | None = None,
    ocr_labels: Sequence[str] | None = None,
) -> Iterable[List[ObservedElement]]:
    """Yield observations for each captured frame."""
    for frame in screen_stream(fps):
        yield analyze_frame(frame, model_path=model_path, ocr_labels=ocr_labels)


__all__ = [
    "capture_screen",
    "screen_stream",
    "detect_gui_elements",
    "extract_text",
    "analyze_frame",
    "observe_screen",
    "ObservedElement",
]
