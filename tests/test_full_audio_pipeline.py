import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types

sf_stub = types.ModuleType("soundfile")
sf_stub.write = lambda *a, **k: None
sf_stub.read = lambda *a, **k: (np.zeros(1), 44100)
sys.modules.setdefault("soundfile", sf_stub)

import qnl_engine
import audio_ingestion
import dsp_engine
import music_generation
import vector_memory


def test_full_audio_pipeline(monkeypatch, tmp_path):
    logs = []

    # Capture vector memory logging
    monkeypatch.setattr(
        vector_memory, "add_vector", lambda text, meta: logs.append(meta["stage"])
    )

    # Stub heavy dependencies
    monkeypatch.setattr(dsp_engine, "_apply_ffmpeg_filter", lambda d, sr, f: (d, sr))
    monkeypatch.setattr(
        music_generation,
        "hf_pipeline",
        lambda task, model: (lambda prompt: [{"audio": b"WAV"}]),
    )
    monkeypatch.setattr(music_generation, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        audio_ingestion.librosa.feature, "mfcc", lambda y, sr: np.zeros((2, 2))
    )

    # 1. QNL song
    phrases, wave = qnl_engine.hex_to_song(
        "00ff", duration_per_byte=0.01, sample_rate=8000
    )
    vector_memory.add_vector("song", {"stage": "qnl"})
    assert wave.dtype == np.int16

    # 2. MFCC extraction
    feats = audio_ingestion.extract_mfcc(wave.astype(np.float32) / 32767, 8000)
    vector_memory.add_vector("mfcc", {"stage": "features"})
    assert feats.shape == (2, 2)

    # 3. Pitch shift
    shifted, sr = dsp_engine.pitch_shift(wave.astype(np.float32), 8000, 1.0)
    vector_memory.add_vector("pitch", {"stage": "dsp"})
    assert sr == 8000

    # 4. Generate music from text
    out = music_generation.generate_from_text("calm melody")
    vector_memory.add_vector("gen", {"stage": "music"})
    assert out.exists()

    assert logs == ["qnl", "features", "dsp", "music"]
