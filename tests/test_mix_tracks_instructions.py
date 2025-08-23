"""Tests for mix tracks instructions."""

from __future__ import annotations

import json
import sys

import numpy as np
import soundfile as sf

from audio.mix_tracks import dsp_engine, main


def test_mix_tracks_json_instructions(tmp_path, monkeypatch):
    sr = 44100
    t = np.linspace(0, 0.25, sr // 4, endpoint=False)
    tone1 = 0.5 * np.sin(2 * np.pi * 220 * t)
    tone2 = 0.5 * np.sin(2 * np.pi * 440 * t)
    wav1 = tmp_path / "tone1.wav"
    wav2 = tmp_path / "tone2.wav"
    sf.write(wav1, tone1, sr)
    sf.write(wav2, tone2, sr)

    instructions = {
        "stems": [
            {
                "file": str(wav1),
                "pitch": 1.0,
                "time": 1.0,
                "compress": {"threshold": -20},
            },
            {"file": str(wav2), "pitch": -1.0},
        ],
        "output": "final.wav",
        "preview": {"file": "preview.wav", "duration": 0.1},
    }
    inst_path = tmp_path / "instr.json"
    inst_path.write_text(json.dumps(instructions))

    # Avoid calling external DSP backends during the test
    monkeypatch.setattr(dsp_engine, "pitch_shift", lambda d, s, p: (d, s))
    monkeypatch.setattr(dsp_engine, "time_stretch", lambda d, s, r: (d, s))
    monkeypatch.setattr(dsp_engine, "compress", lambda d, s, th, ra: (d, s))

    argv_backup = sys.argv.copy()
    monkeypatch.chdir(tmp_path)
    sys.argv = ["mix_tracks.py", "--instructions", str(inst_path)]
    try:
        main()
    finally:
        sys.argv = argv_backup

    out_dir = tmp_path / "output"
    assert (out_dir / "final.wav").exists()
    assert (out_dir / "preview.wav").exists()
