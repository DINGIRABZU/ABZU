"""Generate speech using gTTS with emotion-based style adjustments."""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import librosa

from .utils import save_wav, load_audio, sentiment_score
from .voice_evolution import get_voice_params, update_voice_from_history
from . import tts_coqui, tts_tortoise, tts_bark, tts_xtts
from .emotion_analysis import emotion_to_archetype
from tools import voice_conversion

try:
    from gtts import gTTS
except Exception:  # pragma: no cover - optional dependency
    gTTS = None  # type: ignore

try:
    import openvoice
except Exception:  # pragma: no cover - optional dependency
    openvoice = None

try:  # optional playback dependency
    import sounddevice as sd
except Exception:  # pragma: no cover - optional dependency
    sd = None

logger = logging.getLogger(__name__)


def _sine_placeholder(text: str) -> Tuple[np.ndarray, int]:
    """Return a simple sine wave when gTTS is unavailable."""
    duration = max(1.0, len(text) / 20)
    sr = 22050
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = 0.1 * np.sin(2 * np.pi * 220 * t)
    return wave.astype(np.float32), sr


def convert_voice(wave: np.ndarray, sr: int, timbre: str) -> np.ndarray:
    """Apply a basic voice conversion or pitch shift for ``timbre``."""
    if openvoice is not None:
        try:  # pragma: no cover - external library
            converter = openvoice.VoiceConverter(target=timbre)
            return converter.convert(wave, sr=sr)
        except Exception as exc:  # pragma: no cover - external call may fail
            logger.warning("OpenVoice conversion failed: %s", exc)
    shift = {"soft": -2, "bright": 2}.get(timbre, 0)
    if shift:
        wave = librosa.effects.pitch_shift(wave, sr=sr, n_steps=shift)
    return wave


def _apply_style(wave: np.ndarray, sr: int, style: Dict[str, float]) -> np.ndarray:
    """Apply pitch shift and speed change according to ``style``."""
    pitch = style.get("pitch", 0.0)
    speed = style.get("speed", 1.0)
    if pitch:
        wave = librosa.effects.pitch_shift(wave, sr=sr, n_steps=pitch)
    if speed and speed != 1.0:
        wave = librosa.effects.time_stretch(wave, rate=speed)
    return wave


def _synthesize_gtts(
    text: str,
    emotion: str,
    history: Iterable[Dict[str, Any]] | None = None,
    timbre: str = "neutral",
) -> str:
    """Synthesize ``text`` to a WAV file styled by ``emotion``."""
    style = get_voice_params(emotion)
    entries = list(history) if history else []
    entries.append(
        {
            "emotion": emotion,
            "arousal": 0.5,
            "valence": 0.5,
            "sentiment": sentiment_score(text),
        }
    )
    archetype = emotion_to_archetype(emotion)
    out_path = Path(tempfile.gettempdir()) / f"gtts_{abs(hash(text))}.wav"

    if gTTS is None:
        wave, sr = _sine_placeholder(f"{archetype} {text}")
    else:
        try:
            mp3_a = out_path.with_suffix(".arch.mp3")
            mp3_b = out_path.with_suffix(".text.mp3")
            gTTS(text=archetype).save(str(mp3_a))
            gTTS(text=text).save(str(mp3_b))
            wave_a, sr = librosa.load(str(mp3_a), sr=None, mono=True)
            wave_b, sr_b = librosa.load(str(mp3_b), sr=None, mono=True)
            mp3_a.unlink(missing_ok=True)
            mp3_b.unlink(missing_ok=True)
            if sr_b != sr:
                wave_b = librosa.resample(wave_b, sr_b, sr)
            pause = np.zeros(int(sr * 0.2), dtype=np.float32)
            wave = np.concatenate([wave_a, pause, wave_b])
        except Exception as exc:  # pragma: no cover - external call may fail
            logger.warning("gTTS synthesis failed: %s", exc)
            wave, sr = _sine_placeholder(f"{archetype} {text}")

    wave = _apply_style(wave, sr, style)
    wave = convert_voice(wave, sr, timbre)
    save_wav(wave, str(out_path), sr=sr)
    update_voice_from_history(entries)
    return str(out_path)


def synthesize_speech(
    text: str,
    emotion: str,
    history: Iterable[Dict[str, Any]] | None = None,
    timbre: str = "neutral",
) -> str:
    """Dispatch to the configured TTS backend."""
    backend = os.getenv("CROWN_TTS_BACKEND", "gtts").lower()
    if backend == "coqui":
        return tts_coqui.synthesize_speech(text, emotion)
    if backend == "tortoise":
        return tts_tortoise.synthesize(text, emotion)
    if backend == "bark":
        return tts_bark.synthesize(text, emotion)
    if backend == "xtts":
        return tts_xtts.synthesize(text, emotion)
    return _synthesize_gtts(text, emotion, history, timbre)


def play_wav(path: str) -> None:
    """Play a WAV file if a playback backend is available."""
    if sd is None:
        logger.warning("sounddevice library not installed; cannot play audio")
        return
    wave, sr = load_audio(path, sr=None, mono=True)
    sd.play(wave, sr)
    sd.wait()


class SpeakingEngine:
    """Wrapper that synthesizes and plays speech."""

    def synthesize(
        self,
        text: str,
        emotion: str,
        history: Iterable[Dict[str, Any]] | None = None,
        timbre: str = "neutral",
    ) -> str:
        """Return a path to synthesized speech for ``text``."""
        path = Path(synthesize_speech(text, emotion, history, timbre))
        preset = os.getenv("RVC_PRESET")
        if preset:
            try:  # pragma: no cover - external binary
                path = voice_conversion.apply_rvc(path, preset)
            except Exception:
                logger.exception("RVC conversion failed")
        if os.getenv("VOICEFIX"):
            try:  # pragma: no cover - external binary
                path = voice_conversion.voicefix(path)
            except Exception:
                logger.exception("Voicefix failed")
        return str(path)

    def play(self, path: str) -> None:
        """Play an existing WAV file."""
        play_wav(path)

    def speak(
        self,
        text: str,
        emotion: str,
        history: Iterable[Dict[str, Any]] | None = None,
        timbre: str = "neutral",
        reflect: bool = False,
    ) -> str:
        """Synthesize speech and play it immediately."""
        path = self.synthesize(text, emotion, history, timbre)
        self.play(path)
        if reflect:
            try:  # pragma: no cover - optional reflection path
                from .speech_loopback_reflector import reflect as _reflect

                _reflect(path)
            except Exception:
                logger.exception("speech reflection failed")
        return path

    def stream(
        self,
        text: str,
        emotion: str,
        history: Iterable[Dict[str, Any]] | None = None,
        timbre: str = "neutral",
        segment_duration: float = 0.3,
    ) -> Iterable[Tuple[np.ndarray, int]]:
        """Yield short audio segments for low-latency playback."""
        path = self.synthesize(text, emotion, history, timbre)
        wave, sr = load_audio(path, sr=None, mono=True)
        step = int(sr * segment_duration)
        for start in range(0, len(wave), step):
            yield wave[start : start + step], sr


__all__ = [
    "synthesize_speech",
    "play_wav",
    "convert_voice",
    "SpeakingEngine",
]
