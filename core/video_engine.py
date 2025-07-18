from __future__ import annotations

"""Avatar video generation utilities."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional
import logging
import numpy as np
import tomllib

try:  # pragma: no cover - optional
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional
    cv2 = None  # type: ignore

try:  # pragma: no cover - optional
    from wav2lip import Wav2LipPredictor  # type: ignore
except Exception:  # pragma: no cover - optional
    Wav2LipPredictor = None  # type: ignore

try:  # pragma: no cover - optional
    from sadtalker import SadTalkerPipeline  # type: ignore
except Exception:  # pragma: no cover - optional
    SadTalkerPipeline = None  # type: ignore

try:  # pragma: no cover - optional
    import librosa
except Exception:  # pragma: no cover - optional
    librosa = None  # type: ignore

from .facial_expression_controller import apply_expression
import emotional_state
from . import context_tracker

try:  # pragma: no cover - optional dependency
    import mediapipe as mp
except Exception:  # pragma: no cover - optional dependency
    mp = None  # type: ignore

try:  # pragma: no cover - optional gesture backends
    import controlnet  # type: ignore
except Exception:  # pragma: no cover - optional gesture backends
    controlnet = None  # type: ignore

try:  # pragma: no cover - optional gesture backends
    import animatediff  # type: ignore
except Exception:  # pragma: no cover - optional gesture backends
    animatediff = None  # type: ignore

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "guides" / "avatar_config.toml"


@dataclass
class AvatarTraits:
    """Simple avatar trait configuration."""

    eye_color: tuple[int, int, int] = (0, 255, 0)
    sigil: str = ""
    skins: dict[str, str] = field(default_factory=dict)


def _load_traits() -> AvatarTraits:
    if not _CONFIG_PATH.exists():
        logger.warning("Avatar config missing: %s", _CONFIG_PATH)
        return AvatarTraits()
    data = tomllib.loads(_CONFIG_PATH.read_text())
    eye_color = data.get("eye_color", [0, 255, 0])
    if isinstance(eye_color, list) and len(eye_color) == 3:
        eye = tuple(int(v) for v in eye_color)
    else:
        eye = (0, 255, 0)
    sigil = str(data.get("sigil", ""))
    skins = data.get("skins", {})
    if isinstance(skins, dict):
        skins = {str(k): str(v) for k, v in skins.items()}
    else:
        skins = {}
    return AvatarTraits(eye, sigil, skins)


def _get_face_mesh() -> Optional[object]:  # pragma: no cover - optional
    if mp is None:
        return None
    return mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False, refine_landmarks=True
    )


def _upscale(frame: np.ndarray, scale: int) -> np.ndarray:
    if scale <= 1:
        return frame
    if cv2 is not None:
        return cv2.resize(frame, (frame.shape[1] * scale, frame.shape[0] * scale))
    return frame.repeat(scale, axis=0).repeat(scale, axis=1)


def _skin_color(name: str) -> np.ndarray:
    """Return a deterministic RGB colour derived from ``name``."""
    value = abs(hash(name)) & 0xFFFFFF
    return np.array([(value >> 16) & 255, (value >> 8) & 255, value & 255], dtype=np.uint8)


def generate_avatar_stream(
    scale: int = 1, lip_sync_audio: Optional[Path] = None
) -> Iterator[np.ndarray]:
    """Yield RGB frames representing the configured avatar."""
    traits = _load_traits()
    color = np.array(traits.eye_color, dtype=np.uint8)
    mesh = _get_face_mesh()

    audio_wave = None
    step = 0
    predictor = None
    idx = 0
    sadtalker_frames = None
    if lip_sync_audio is not None and SadTalkerPipeline is not None:
        try:  # pragma: no cover - optional
            pipeline = SadTalkerPipeline()
            sadtalker_frames = iter(pipeline.generate(str(lip_sync_audio)))
        except Exception:  # pragma: no cover - optional
            logger.exception("Failed to initialise SadTalker")
            sadtalker_frames = None
    if (
        sadtalker_frames is None
        and lip_sync_audio is not None
        and librosa is not None
        and Wav2LipPredictor is not None
    ):
        try:
            audio_wave, sr = librosa.load(str(lip_sync_audio), sr=16000, mono=True)
            step = sr // 15
            predictor = Wav2LipPredictor()
        except Exception:  # pragma: no cover - optional
            logger.exception("Failed to initialise Wav2Lip")

    try:
        while True:
            if sadtalker_frames is not None:
                try:
                    frame = next(sadtalker_frames)
                    frame = np.asarray(frame, dtype=np.uint8)
                except StopIteration:
                    break
            else:
                layer = emotional_state.get_current_layer() or ""
                skin = traits.skins.get(layer)
                frame = np.zeros((64, 64, 3), dtype=np.uint8)
                frame[:] = _skin_color(skin) if skin else color
                if context_tracker.state.avatar_loaded:
                    emotion = emotional_state.get_last_emotion()
                    frame = apply_expression(frame, emotion)
                    if mesh is not None:
                        _ = mesh.process(frame)

                if predictor is not None and audio_wave is not None:
                    seg = audio_wave[idx : idx + step]
                    idx += step
                    try:
                        frame = predictor.synthesize(frame, seg)
                    except Exception:  # pragma: no cover - optional
                        logger.exception("Wav2Lip synthesis failed")

            if controlnet is not None:
                try:
                    frame = controlnet.apply_gesture(frame)  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover - optional
                    logger.exception("ControlNet gesture failed")
            elif animatediff is not None:
                try:
                    frame = animatediff.apply_gesture(frame)  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover - optional
                    logger.exception("AnimateDiff gesture failed")

            frame = _upscale(frame, scale)
            yield frame
    finally:
        if mesh is not None:
            mesh.close()


def start_stream(
    scale: int = 1, lip_sync_audio: Optional[Path] = None
) -> Iterator[np.ndarray]:
    """Return an iterator producing avatar frames."""

    return generate_avatar_stream(scale=scale, lip_sync_audio=lip_sync_audio)


__all__ = ["start_stream", "generate_avatar_stream", "AvatarTraits"]
