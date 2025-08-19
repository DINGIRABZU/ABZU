from __future__ import annotations

"""Storage utilities for raw physical inputs."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
import logging

from aspect_processor import analyze_phonetic, analyze_semantic

try:  # pragma: no cover - optional
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional
    cv2 = None  # type: ignore

try:  # pragma: no cover - optional
    import librosa  # type: ignore
except Exception:  # pragma: no cover - optional
    librosa = None  # type: ignore

try:  # pragma: no cover - optional
    import whisper  # type: ignore
except Exception:  # pragma: no cover - optional
    whisper = None  # type: ignore


logger = logging.getLogger(__name__)
_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "physical"


@dataclass
class PhysicalEvent:
    """Container for raw physical inputs.

    ``data`` may contain arrays for audio/video or plain text for ``text`` events.
    """

    modality: str
    data: Any | str
    sample_rate: Optional[int] = None


def store_physical_event(event: PhysicalEvent) -> Path:
    """Persist a physical event and accompanying metadata.

    The raw input is serialized under ``data/physical`` and a JSON metadata file
    containing the timestamp and modality is written alongside it.
    """

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat()
    base = f"{timestamp}_{event.modality}"
    meta: dict[str, Any] = {"timestamp": timestamp, "modality": event.modality}

    if event.modality == "video":
        if cv2 is None:
            raise RuntimeError("OpenCV is required for video events")
        frame = event.data
        file_path = _DATA_DIR / f"{base}.png"
        cv2.imwrite(str(file_path), frame)
        meta["file"] = file_path.name
    elif event.modality == "audio":
        if librosa is None:
            raise RuntimeError("librosa is required for audio events")
        if event.sample_rate is None:
            raise ValueError("sample_rate required for audio events")
        audio = librosa.util.normalize(event.data)
        file_path = _DATA_DIR / f"{base}.wav"
        try:  # pragma: no cover - optional
            import soundfile as sf

            sf.write(str(file_path), audio, event.sample_rate)
        except Exception as exc:  # pragma: no cover - optional
            raise RuntimeError("soundfile is required to store audio") from exc
        meta["file"] = file_path.name
        if whisper is not None:
            try:  # pragma: no cover - optional
                model = whisper.load_model("base")
                result = model.transcribe(str(file_path))
                meta["transcription"] = result.get("text", "").strip()
            except Exception:  # pragma: no cover - optional
                logger.exception("Whisper transcription failed")
    elif event.modality == "text":
        if not isinstance(event.data, str):
            raise ValueError("text events require string data")
        file_path = _DATA_DIR / f"{base}.txt"
        file_path.write_text(event.data, encoding="utf-8")
        meta["file"] = file_path.name
        analyze_phonetic(event.data)
        analyze_semantic(event.data)
    else:
        raise ValueError(f"Unknown modality: {event.modality}")

    meta_path = _DATA_DIR / f"{base}.json"
    meta_path.write_text(json.dumps(meta))
    return meta_path


__all__ = ["PhysicalEvent", "store_physical_event"]
