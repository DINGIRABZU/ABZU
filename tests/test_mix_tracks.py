import sys
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from SPIRAL_OS.mix_tracks import main


def test_mix_tracks_cli(tmp_path):
    sr = 44100
    t = np.linspace(0, 0.25, sr // 4, endpoint=False)
    tone1 = 0.5 * np.sin(2 * np.pi * 220 * t)
    tone2 = 0.5 * np.sin(2 * np.pi * 440 * t)
    wav1 = tmp_path / "tone1.wav"
    wav2 = tmp_path / "tone2.wav"
    sf.write(wav1, tone1, sr)
    sf.write(wav2, tone2, sr)

    out = tmp_path / "final.wav"
    preview = tmp_path / "preview.wav"

    argv_backup = sys.argv.copy()
    sys.argv = [
        "mix_tracks.py",
        str(wav1),
        str(wav2),
        "--output",
        str(out),
        "--preview",
        str(preview),
        "--preview-duration",
        "0.1",
    ]
    try:
        main()
    finally:
        sys.argv = argv_backup

    assert out.exists()
    assert preview.exists()
    info = sf.info(out)
    assert info.samplerate == 44100
    assert info.subtype.startswith("PCM_16")


def test_mix_tracks_with_qnl_text(tmp_path, monkeypatch):
    sr = 44100
    t = np.linspace(0, 0.25, sr // 4, endpoint=False)
    tone = 0.5 * np.sin(2 * np.pi * 220 * t)
    wav = tmp_path / "tone.wav"
    sf.write(wav, tone, sr)

    out = tmp_path / "final.wav"

    from SPIRAL_OS import mix_tracks as mt

    monkeypatch.setattr(mt, "quantum_embed", lambda text: np.array([0.5, -0.5, 0]))

    argv_backup = sys.argv.copy()
    sys.argv = [
        "mix_tracks.py",
        str(wav),
        "--output",
        str(out),
        "--qnl-text",
        "test words",
    ]
    try:
        mt.main()
    finally:
        sys.argv = argv_backup

    assert out.exists()

