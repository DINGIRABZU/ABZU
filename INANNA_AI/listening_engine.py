from __future__ import annotations

"""Real-time microphone listening with basic feature extraction."""

import logging
import tempfile
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, Generator, Optional, Tuple
import asyncio
import json

import numpy as np
import librosa

try:
    import opensmile
except Exception:  # pragma: no cover - optional dependency
    opensmile = None

try:
    import websockets
except Exception:  # pragma: no cover - optional dependency
    websockets = None

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - optional dependency
    sd = None

from . import utils, emotion_analysis, silence_reflection
import emotional_state


logger = logging.getLogger(__name__)


def _infer_dialect(pitch: float) -> str:
    """Return a crude dialect label based on ``pitch``."""
    if pitch < 150:
        return "lowland"
    if pitch > 300:
        return "upland"
    return "neutral"


_SMILE: opensmile.Smile | None = None


def _get_smile() -> opensmile.Smile | None:
    """Return a cached ``opensmile.Smile`` instance if available."""
    global _SMILE
    if _SMILE is None and opensmile is not None:
        _SMILE = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.Functionals,
        )
    return _SMILE


def _extract_features(wave: np.ndarray, sr: int) -> Dict[str, float]:
    """Return pitch, tempo, emotion and other features for ``wave``."""
    if len(wave) == 0:
        return {
            "emotion": "neutral",
            "pitch": 0.0,
            "tempo": 0.0,
            "classification": "silence",
            "silence_meaning": silence_reflection.silence_meaning(wave, sr),
            "dialect": "neutral",
            "weight": emotion_analysis.emotion_weight("neutral"),
        }

    f0 = librosa.yin(
        wave,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )
    pitch = float(np.nanmean(f0))
    tempo, _ = librosa.beat.beat_track(y=wave, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])

    energy = float(np.mean(wave ** 2))
    classification = "silence"
    if energy > 1e-4:
        classification = "speech" if 80 <= pitch <= 300 else "noise"

    silence_meaning = ""
    if classification == "silence":
        silence_meaning = silence_reflection.silence_meaning(wave, sr)

    amp = float(np.mean(np.abs(wave)))
    emotion = "neutral"
    arousal: float | None = None
    valence: float | None = None

    smile = _get_smile()
    if smile is not None:
        feats = smile.process_signal(wave.astype(np.float32), sr).iloc[0]
        loudness = float(feats.get("loudness_sma3_amean", 0.0))
        hnr = float(feats.get("HNRdBACF_sma3nz_amean", 0.0))
        arousal = max(0.0, min(1.0, (loudness + 60.0) / 60.0))
        valence = max(0.0, min(1.0, (hnr + 20.0) / 40.0))

    if arousal is not None and valence is not None:
        if arousal > 0.75:
            emotion = "stress"
        elif valence < 0.3 and arousal > 0.5:
            emotion = "fear"
        elif valence > 0.7 and arousal > 0.5:
            emotion = "joy"
        elif valence < 0.4 and arousal < 0.4:
            emotion = "sad"
    if emotion == "neutral":
        if amp > 0.4:
            emotion = "stress"
        elif pitch > 400 and amp < 0.1:
            emotion = "fear"
        elif pitch > 300 and amp > 0.2:
            emotion = "joy"
        elif pitch < 160 and amp < 0.1:
            emotion = "sad"
        elif pitch > 180 and tempo > 120:
            emotion = "excited"
        elif pitch < 120 and tempo < 90:
            emotion = "calm"

    dialect = _infer_dialect(pitch)
    weight = emotion_analysis.emotion_weight(emotion)

    return {
        "emotion": emotion,
        "arousal": None if arousal is None else round(arousal, 3),
        "valence": None if valence is None else round(valence, 3),
        "pitch": round(pitch, 2),
        "tempo": round(tempo, 2),
        "classification": classification,
        "silence_meaning": silence_meaning,
        "dialect": dialect,
        "weight": weight,
    }


class ListeningEngine:
    """Stream audio from the microphone and yield analysis for each chunk."""

    def __init__(self, sr: int = 44100, chunk_duration: float = 0.5) -> None:
        if sd is None:
            raise RuntimeError("sounddevice library not installed")
        self.sr = sr
        self.chunk_size = int(sr * chunk_duration)
        self._queue: "Queue[np.ndarray]" = Queue()
        self._stream: Optional[sd.InputStream] = None
        self.state: Dict[str, float] = {
            "emotion": "neutral",
            "weight": emotion_analysis.emotion_weight("neutral"),
        }

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:  # pragma: no cover - external callback
        if status:
            logger.warning("InputStream status: %s", status)
        self._queue.put(indata[:, 0].copy())

    def __enter__(self) -> "ListeningEngine":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        """Start streaming from the microphone."""
        if self._stream is not None:
            return
        self._stream = sd.InputStream(
            samplerate=self.sr,
            channels=1,
            blocksize=self.chunk_size,
            callback=self._callback,
        )
        self._stream.start()
        logger.info("Listening engine started")

    def stop(self) -> None:
        """Stop the microphone stream."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            logger.info("Listening engine stopped")

    def stream_chunks(self, duration: Optional[float] = None) -> Generator[Tuple[np.ndarray, Dict[str, float]], None, None]:
        """Yield (waveform, features) tuples for each audio chunk."""
        if self._stream is None:
            self.start()
        total_frames = int(duration * self.sr) if duration else None
        frames_read = 0
        while total_frames is None or frames_read < total_frames:
            try:
                chunk = self._queue.get(timeout=duration)
            except Empty:
                continue
            frames_read += len(chunk)
            features = _extract_features(chunk, self.sr)
            emotional_state.set_last_emotion(features.get("emotion"))
            self.state = features
            yield chunk, features
            if total_frames is not None and frames_read >= total_frames:
                break

    def record(self, duration: float) -> Tuple[str, Dict[str, float]]:
        """Capture ``duration`` seconds of audio and return file path and last state."""
        chunks = []
        for chunk, state in self.stream_chunks(duration):
            chunks.append(chunk)
            self.state = state
        last_state = self.state
        wave = np.concatenate(chunks) if chunks else np.array([], dtype=np.float32)
        path = Path(tempfile.gettempdir()) / "inanna_stream.wav"
        utils.save_wav(wave.astype(np.float32), str(path), sr=self.sr)
        return str(path), last_state


def capture_audio(duration: float, sr: int = 44100) -> Tuple[np.ndarray, bool]:
    """Record raw audio for ``duration`` seconds and report silence."""
    if sd is None:
        raise RuntimeError("sounddevice library not installed")
    data = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    audio = data[:, 0]
    is_silent = float(np.mean(np.abs(audio))) < 1e-4
    return audio, is_silent


def analyze_audio(duration: float, sr: int = 44100) -> Tuple[np.ndarray, Dict[str, float]]:
    """Capture audio and return the features."""
    audio, silent = capture_audio(duration, sr)
    info = _extract_features(audio, sr)
    info["is_silent"] = silent
    return audio, info


async def _websocket_handler(websocket) -> None:
    """Stream features over ``websocket`` from the microphone."""
    engine = ListeningEngine()
    gen = engine.stream_chunks()
    async with engine:
        while True:
            chunk, features = await asyncio.to_thread(next, gen)
            await websocket.send(json.dumps(features))


async def start_websocket_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    """Start a WebSocket server streaming microphone analysis."""
    if websockets is None:
        raise RuntimeError("websockets library not installed")
    async with websockets.serve(_websocket_handler, host, port):
        logger.info("WebSocket server listening on %s:%d", host, port)
        await asyncio.Future()


__all__ = [
    "ListeningEngine",
    "capture_audio",
    "analyze_audio",
    "start_websocket_server",
]

