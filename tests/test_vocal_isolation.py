import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import vocal_isolation


def _setup_fake_tempdir(tmp_path, monkeypatch):
    out_dir = tmp_path / "out"
    def fake_mkdtemp(prefix="stems_"):
        out_dir.mkdir()
        return str(out_dir)
    monkeypatch.setattr(vocal_isolation.tempfile, "mkdtemp", fake_mkdtemp)
    return out_dir


def test_separate_stems_demucs(monkeypatch, tmp_path):
    out_dir = _setup_fake_tempdir(tmp_path, monkeypatch)

    calls = {}
    def fake_run(cmd, check):
        calls["cmd"] = cmd
        (out_dir / "vocals.wav").write_text("x")
        (out_dir / "drums.wav").write_text("x")
    monkeypatch.setattr(vocal_isolation.subprocess, "run", fake_run)

    stems = vocal_isolation.separate_stems(Path("song.wav"))

    assert calls["cmd"] == [
        "python3", "-m", "demucs.separate", "-o", str(out_dir), "song.wav"
    ]
    assert stems["vocals"] == out_dir / "vocals.wav"
    assert stems["drums"] == out_dir / "drums.wav"


def test_separate_stems_spleeter(monkeypatch, tmp_path):
    out_dir = _setup_fake_tempdir(tmp_path, monkeypatch)

    calls = {}
    def fake_run(cmd, check):
        calls["cmd"] = cmd
        (out_dir / "vocals.wav").write_text("x")
    monkeypatch.setattr(vocal_isolation.subprocess, "run", fake_run)

    stems = vocal_isolation.separate_stems(Path("song.mp3"), method="spleeter")

    assert calls["cmd"] == [
        "spleeter", "separate", "-p", "spleeter:5stems", "-o", str(out_dir), "song.mp3"
    ]
    assert stems["vocals"] == out_dir / "vocals.wav"


def test_separate_stems_umx(monkeypatch, tmp_path):
    out_dir = _setup_fake_tempdir(tmp_path, monkeypatch)

    calls = {}
    def fake_run(cmd, check):
        calls["cmd"] = cmd
        (out_dir / "bass.wav").write_text("x")
    monkeypatch.setattr(vocal_isolation.subprocess, "run", fake_run)

    stems = vocal_isolation.separate_stems(Path("song.flac"), method="umx")

    assert calls["cmd"] == ["umx", "song.flac", "--outdir", str(out_dir)]
    assert stems["bass"] == out_dir / "bass.wav"

