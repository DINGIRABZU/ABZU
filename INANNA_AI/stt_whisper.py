"""Speech-to-text helpers using the Whisper library."""
from __future__ import annotations

try:
    import whisper
except Exception:  # pragma: no cover - optional dependency
    whisper = None  # type: ignore

from .config import WHISPER_MODEL, WHISPER_MODEL_DIR

# Lazily loaded Whisper model instance
_model: whisper.model.Whisper | None = None


def _get_model() -> whisper.model.Whisper:
    """Load the Whisper model specified in :mod:`config` if needed."""
    global _model
    if _model is None:
        if whisper is None:
            raise RuntimeError("whisper library not installed")
        WHISPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        _model = whisper.load_model(WHISPER_MODEL, download_root=str(WHISPER_MODEL_DIR))
    return _model


def transcribe_audio(audio_path: str) -> str:
    """Transcribe ``audio_path`` and return the recognized text."""
    model = _get_model()
    result = model.transcribe(audio_path)
    return result.get("text", "").strip()


__all__ = ["transcribe_audio"]
