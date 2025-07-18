import sys
import os
import json
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from SPIRAL_OS import seven_dimensional_music as sdm

DUMMY_PLANES = {
    "physical": {},
    "emotional": {},
    "mental": {},
    "astral": {},
    "etheric": {},
    "celestial": {},
    "divine": {},
}


def test_cli_creates_final_track(tmp_path):
    sr = 44100
    t = np.linspace(0, 0.25, sr // 4, endpoint=False)
    tone = np.sin(2 * np.pi * 220 * t)
    wav_path = tmp_path / "tone.wav"
    sf.write(wav_path, tone, sr)

    out = tmp_path / "final.wav"
    argv_backup = sys.argv.copy()
    sys.argv = [
        "seven_dimensional_music.py",
        str(wav_path),
        "--output",
        str(out),
    ]
    try:
        monkeypatch = __import__('pytest').MonkeyPatch()
        monkeypatch.setattr(sdm, "analyze_seven_planes", lambda *a, **k: DUMMY_PLANES)
        sdm.main()
        monkeypatch.undo()
    finally:
        sys.argv = argv_backup

    assert out.exists()
    jpath = out.with_suffix(".json")
    assert jpath.exists()
    data = json.loads(jpath.read_text())
    assert set(data["planes"]) == {
        "physical",
        "emotional",
        "mental",
        "astral",
        "etheric",
        "celestial",
        "divine",
    }
    assert data["planes"]["physical"]["element"] == "bass"

def test_cli_secret_message(tmp_path):
    sr = 44100
    t = np.linspace(0, 0.25, sr // 4, endpoint=False)
    tone = np.sin(2 * np.pi * 220 * t)
    wav_path = tmp_path / "tone.wav"
    sf.write(wav_path, tone, sr)

    out = tmp_path / "final.wav"
    secret = "hello"
    argv_backup = sys.argv.copy()
    cwd = os.getcwd()
    sys.argv = [
        "seven_dimensional_music.py",
        str(wav_path),
        "--output",
        str(out),
        "--secret",
        secret,
    ]
    try:
        os.chdir(tmp_path)
        monkeypatch = __import__('pytest').MonkeyPatch()
        monkeypatch.setattr(sdm, "analyze_seven_planes", lambda *a, **k: DUMMY_PLANES)
        sdm.main()
        monkeypatch.undo()
    finally:
        os.chdir(cwd)
        sys.argv = argv_backup

    from MUSIC_FOUNDATION.synthetic_stego import extract_data
    hidden = extract_data(tmp_path / "human_layer.wav")
    assert hidden == secret
    jpath = out.with_suffix(".json")
    assert jpath.exists()


def test_quantum_music_changes_with_context(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sdm,
        "quantum_embed",
        lambda text: np.array([len(text)], dtype=float),
    )
    monkeypatch.setattr(
        sdm,
        "embedding_to_params",
        lambda emb: (emb[0] * 0.01, 1.0 + emb[0] * 0.01, 1.0),
    )
    monkeypatch.setattr(
        sdm.qnl_engine,
        "hex_to_song",
        lambda *a, **k: ([], np.ones(100, dtype=np.int16)),
    )
    monkeypatch.setattr(sdm, "analyze_seven_planes", lambda *a, **k: DUMMY_PLANES)
    monkeypatch.setattr(sdm.emotion_analysis, "emotion_weight", lambda e: 0.5)

    p1 = sdm.generate_quantum_music("alpha", "joy", output_dir=tmp_path)
    p2 = sdm.generate_quantum_music("beta", "sad", output_dir=tmp_path)
    assert p1 != p2
    w1, _ = sf.read(p1, always_2d=False)
    w2, _ = sf.read(p2, always_2d=False)
    assert w1.shape != w2.shape or not np.allclose(w1, w2)


def test_generate_quantum_music_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sdm,
        "quantum_embed",
        lambda text: np.zeros(3, dtype=float),
    )
    monkeypatch.setattr(
        sdm,
        "embedding_to_params",
        lambda emb: (0.0, 1.0, 1.0),
    )
    monkeypatch.setattr(
        sdm.qnl_engine,
        "hex_to_song",
        lambda *a, **k: ([], np.ones(100, dtype=np.int16)),
    )
    monkeypatch.setattr(
        sdm,
        "analyze_seven_planes",
        lambda *a, **k: {
            "physical": {},
            "emotional": {},
            "mental": {},
            "astral": {},
            "etheric": {},
            "celestial": {},
            "divine": {},
        },
    )
    monkeypatch.setattr(sdm.emotion_analysis, "emotion_weight", lambda e: 0.0)

    out = sdm.generate_quantum_music("alpha", "joy", output_dir=tmp_path)
    jpath = out.with_suffix(".json")
    assert jpath.exists()
    data = json.loads(jpath.read_text())
    assert set(data["planes"]) == {
        "physical",
        "emotional",
        "mental",
        "astral",
        "etheric",
        "celestial",
        "divine",
    }
