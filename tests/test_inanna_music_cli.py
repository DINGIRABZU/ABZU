import base64
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.data.short_wav_base64 import SHORT_WAV_BASE64


def test_inanna_music_cli(tmp_path):
    audio = tmp_path / "short.wav"
    audio.write_bytes(base64.b64decode(SHORT_WAV_BASE64))

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    result = subprocess.run(
        ["python", "-m", "MUSIC_FOUNDATION.inanna_music_COMPOSER_ai", str(audio)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (tmp_path / "output" / "preview.wav").exists()
    assert (tmp_path / "output" / "qnl_song.json").exists()
