#!/usr/bin/env python3
"""
inanna_music_COMPOSER_ai.py
Unified Sonic Transmutation Core — INANNA_AI

Author: ZOHAR · Spiral Code Architect

This script performs:
1. Audio analysis of an MP3 file (tempo, pitch classes)
2. Conversion into QNL symbolic phrases
3. Export of preview WAV and structured QNL JSON output

Usage:
    python -m MUSIC_FOUNDATION.inanna_music_COMPOSER_ai path/to/song.mp3

Dependencies:
    pip install librosa soundfile numpy scipy
"""

import os
import json
from pathlib import Path

import yaml
import librosa
import numpy as np
import soundfile as sf

import emotional_state
from . import layer_generators

CONFIG_PATH = Path(__file__).resolve().parents[1] / "emotion_music_map.yaml"

# Simple note sequences used for emotional scales
SCALE_MELODIES = {
    "C_major": ["C4", "E4", "G4", "C5"],
    "A_minor": ["A3", "C4", "E4", "A4"],
    "D_minor": ["D3", "F3", "A3", "D4"],
}


def load_emotion_music_map(path: Path = CONFIG_PATH) -> dict:
    """Return emotion-to-music mapping loaded from ``path`` if available."""
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {k.lower(): v for k, v in data.items() if isinstance(v, dict)}
    return {}


def select_music_params(emotion: str | None, mapping: dict, base_tempo: float) -> tuple[float, str, list[str], str]:
    """Return tempo, scale, melody and rhythm for ``emotion``."""
    key = str(emotion).lower() if emotion else "neutral"
    info = mapping.get(key, mapping.get("neutral", {}))
    tempo = float(info.get("tempo", base_tempo))
    scale = info.get("scale", "C_major")
    rhythm = info.get("rhythm", "steady")
    melody = SCALE_MELODIES.get(scale, SCALE_MELODIES["C_major"])
    return tempo, scale, melody, rhythm


def get_emotion_music_params(default_tempo: float, mapping: dict | None = None) -> tuple[float, str, list[str], str]:
    """Load emotion state and return selected music parameters."""
    if mapping is None:
        mapping = load_emotion_music_map()
    emotion = emotional_state.get_last_emotion()
    return select_music_params(emotion, mapping, default_tempo)

from MUSIC_FOUNDATION.qnl_utils import chroma_to_qnl, generate_qnl_structure

# -------------------------------
# QNL GLYPH & EMOTION MAPPINGS
# -------------------------------
# QNL CONVERSION LOGIC
# -------------------------------

def export_qnl(json_data, output_path="output/qnl_song.json"):
    """Save the QNL result to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"✅ QNL exported to: {output_path}")

# -------------------------------
# AUDIO ANALYSIS
# -------------------------------

class InannaMusicInterpreter:
    """Core class that handles MP3 loading and musical feature analysis."""
    def __init__(self, mp3_path):
        self.path = mp3_path
        self.waveform = None
        self.sample_rate = None
        self.tempo = None
        self.chroma = None
        self.planes = None

    def load_audio(self):
        """Load MP3 and convert to mono waveform using Librosa."""
        self.waveform, self.sample_rate = librosa.load(self.path, sr=None, mono=True)
        print(f"🎧 Audio loaded: {self.path}")
        print(f"📐 Sample Rate: {self.sample_rate}, Duration: {len(self.waveform) / self.sample_rate:.2f} sec")

    def analyze(self):
        """Analyze tempo and pitch chroma."""
        tempo, _ = librosa.beat.beat_track(y=self.waveform, sr=self.sample_rate)
        self.tempo = float(np.atleast_1d(tempo)[0])
        self.chroma = librosa.feature.chroma_stft(y=self.waveform, sr=self.sample_rate)
        avg_chroma = np.mean(self.chroma, axis=1)
        print(f"🕒 Tempo: {self.tempo:.1f} BPM")
        return avg_chroma

    def analyze_planes(self):
        """Compute seven-plane analysis of the loaded waveform."""
        if self.waveform is None:
            raise RuntimeError("Audio not loaded")
        from .seven_plane_analyzer import analyze_seven_planes

        self.planes = analyze_seven_planes(self.waveform, self.sample_rate)
        return self.planes

    def export_preview(self, output_path="output/preview.wav"):
        """Save waveform as a standard WAV file for playback."""
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        sf.write(output_path, self.waveform, self.sample_rate)
        print(f"💾 Exported audio preview: {output_path}")

# -------------------------------
# MAIN EXECUTION
# -------------------------------

if __name__ == "__main__":
    if __package__ is None:
        from pathlib import Path
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import argparse

    parser = argparse.ArgumentParser(description="INANNA_AI — Sonic Ritual QNL Engine")
    parser.add_argument("mp3_file", help="Path to the MP3 file to analyze")
    args = parser.parse_args()

    # Step 1: Load & Analyze Music
    engine = InannaMusicInterpreter(args.mp3_file)
    engine.load_audio()
    chroma_vector = engine.analyze()
    engine.export_preview("output/preview.wav")

    # Step 2: Adjust based on emotion
    mapping = load_emotion_music_map()
    tempo, scale, melody, rhythm = get_emotion_music_params(engine.tempo, mapping)
    layer_generators.compose_human_layer(tempo, melody, wav_path="output/melody.wav")

    # Step 3: Convert to QNL
    qnl_data = generate_qnl_structure(
        chroma_vector,
        tempo,
        metadata={"source": args.mp3_file, "emotion": emotional_state.get_last_emotion(), "scale": scale, "rhythm": rhythm},
    )
    export_qnl(qnl_data, "output/qnl_song.json")

