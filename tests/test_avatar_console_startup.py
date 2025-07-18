import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_avatar_console_startup(monkeypatch):
    calls: list[str] = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(" ".join(cmd) if isinstance(cmd, list) else cmd)
        if cmd[0] == "bash" and str(cmd[1]).endswith("start_avatar_console.sh"):
            scale = os.environ.get("AVATAR_SCALE")
            tail_cmd = "tail -f logs/INANNA_AI.log"
            video_cmd = "python video_stream.py" + (f" --scale {scale}" if scale else "")
            calls.extend(["start_crown_console", video_cmd, tail_cmd])
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def fake_system(cmd):
        calls.append(cmd)
        return 0

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(os, "system", fake_system)
    monkeypatch.setenv("AVATAR_SCALE", "2")

    result = subprocess.run(["bash", str(ROOT / "start_avatar_console.sh")])

    assert result.returncode == 0
    assert "start_crown_console" in calls
    assert "python video_stream.py --scale 2" in calls
    assert "tail -f logs/INANNA_AI.log" in calls
    crown_idx = calls.index("start_crown_console")
    video_idx = calls.index("python video_stream.py --scale 2")
    tail_idx = calls.index("tail -f logs/INANNA_AI.log")

    assert crown_idx < video_idx < tail_idx
