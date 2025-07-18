from __future__ import annotations

"""Mirror reflection loop utilities."""

from pathlib import Path
import json
import logging
import os
from typing import Dict

try:  # pragma: no cover - optional dependency
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cv2 = None  # type: ignore

import numpy as np

from core import video_engine, self_correction_engine
from invocation_engine import invoke_ritual
from corpus_memory_logging import log_ritual_result
import emotional_state
from INANNA_AI import adaptive_learning

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[1] / "mirror_thresholds.json"
CONFIG_ENV_VAR = "MIRROR_THRESHOLDS_PATH"


def load_thresholds() -> Dict[str, float]:
    """Return mirror thresholds from ``MIRROR_THRESHOLDS_PATH`` or
    :data:`CONFIG_PATH`."""
    path_str = os.getenv(CONFIG_ENV_VAR)
    path = Path(path_str) if path_str else CONFIG_PATH
    if not path.exists():
        logger.warning("mirror_thresholds missing: %s", path)
        return {"default": 0.0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed reading mirror_thresholds")
        return {"default": 0.0}
    return {str(k): float(v) for k, v in data.items()}


def detect_expression(frame: np.ndarray) -> str:
    """Return a basic expression label for ``frame``."""
    mean = float(frame.mean())
    if mean > 170:
        return "joy"
    if mean < 85:
        return "sadness"
    return "neutral"


def run_reflection_loop(iterations: int = 10) -> None:
    """Compare intended emotion with avatar output and self-correct."""
    thresholds = load_thresholds()
    stream = video_engine.start_stream()
    citrinitas_count = 0
    for _ in range(iterations):
        try:
            frame = next(stream)
        except StopIteration:
            break
        if cv2 is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        detected = detect_expression(frame)
        intended = emotional_state.get_last_emotion() or "neutral"
        reward = 1.0 if detected == intended else -1.0
        adaptive_learning.update_mirror_thresholds(reward)
        thresholds = adaptive_learning.MIRROR_THRESHOLD_AGENT.thresholds
        logger.debug("reflection detected=%s intended=%s", detected, intended)
        if detected == "citrinitas":
            citrinitas_count += 1
            tol = thresholds.get("citrinitas", thresholds.get("default", 0.0))
            if citrinitas_count > tol:
                steps = invoke_ritual("citrinitas_rite")
                log_ritual_result("citrinitas_rite", steps)
                citrinitas_count = 0
            continue
        else:
            citrinitas_count = 0
        if detected != intended:
            tol = thresholds.get(intended, thresholds.get("default", 0.0))
            logger.info(
                "mismatch detected: %s vs %s (tol %.3f)",
                detected,
                intended,
                tol,
            )
            self_correction_engine.adjust(detected, intended, tol)
            logger.info("correction issued from %s to %s", detected, intended)


__all__ = ["run_reflection_loop", "detect_expression", "load_thresholds"]
