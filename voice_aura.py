from __future__ import annotations

"""Apply reverb and timbre effects based on the current emotion."""

from pathlib import Path
import logging
import shutil
import subprocess
import tempfile

import numpy as np
import soundfile as sf

from dsp_engine import rave_morph, nsynth_interpolate
import emotional_state

try:  # pragma: no cover - optional dependency
    from pydub import AudioSegment
except Exception:  # pragma: no cover - optional dependency
    AudioSegment = None  # type: ignore

logger = logging.getLogger(__name__)


# Basic reverb/delay presets per emotion
EFFECT_PRESETS: dict[str, dict[str, int]] = {
    "neutral": {"reverb": 20, "delay": 100},
    "joy": {"reverb": 30, "delay": 80},
    "excited": {"reverb": 25, "delay": 50},
    "calm": {"reverb": 50, "delay": 150},
    "sad": {"reverb": 60, "delay": 200},
    "fear": {"reverb": 70, "delay": 120},
    "stress": {"reverb": 40, "delay": 60},
}


def sox_available() -> bool:
    """Return ``True`` when the ``sox`` binary is available."""
    return shutil.which("sox") is not None


def _apply_pydub_effects(seg: AudioSegment, reverb_ms: int, delay_ms: int) -> AudioSegment:
    """Apply simple delay/reverb effects using :mod:`pydub`."""
    if delay_ms > 0:
        seg = seg.overlay(seg - 6, position=delay_ms)
    if reverb_ms > 0:
        rev = seg.reverse().fade_out(reverb_ms).reverse()
        seg = seg.overlay(rev - 10)
    return seg


def apply_voice_aura(
    path: Path,
    *,
    emotion: str | None = None,
    rave_checkpoint: Path | None = None,
    nsynth_checkpoint: Path | None = None,
    amount: float = 0.5,
) -> Path:
    """Return a processed copy of ``path`` with emotion-derived effects."""

    emotion = (emotion or emotional_state.get_last_emotion() or "neutral").lower()
    params = EFFECT_PRESETS.get(emotion, EFFECT_PRESETS["neutral"])

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = Path(tmp.name)

    if sox_available():
        cmd = [
            "sox",
            str(path),
            str(out_path),
            "reverb",
            str(params["reverb"]),
            "delay",
            f"{params['delay']/1000.0:.3f}",
        ]
        subprocess.run(cmd, check=True)
    elif AudioSegment is not None:  # pragma: no cover - fallback path
        seg = AudioSegment.from_file(path)
        seg = _apply_pydub_effects(seg, params["reverb"], params["delay"])
        seg.export(out_path, format="wav")
    else:  # pragma: no cover - no processing possible
        shutil.copy(path, out_path)

    if rave_checkpoint is not None:
        data, sr = sf.read(out_path, dtype="float32")
        data, sr = rave_morph(data, data, sr, amount, rave_checkpoint)
        sf.write(out_path, data, sr)
    elif nsynth_checkpoint is not None:
        data, sr = sf.read(out_path, dtype="float32")
        data, sr = nsynth_interpolate(data, data, sr, amount, nsynth_checkpoint)
        sf.write(out_path, data, sr)

    logger.info("voice aura applied", extra={"emotion": emotion})
    return out_path


__all__ = ["apply_voice_aura", "sox_available"]
