import os
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_start_avatar_console_waits_and_fallback(monkeypatch):
    calls: list[str] = []

    def fake_run(cmd, *args, **kwargs):
        joined = " ".join(cmd) if isinstance(cmd, list) else cmd
        calls.append(joined)
        if cmd[0] == "bash" and str(cmd[1]).endswith("start_avatar_console.sh"):
            fake_run(["bash", str(ROOT / "start_crown_console.sh")])
            calls.extend(
                [
                    "start_crown_console",
                    "python video_stream.py",
                    "tail -f logs/INANNA_AI.log",
                    "wait crown stream",
                    "kill tail",
                ]
            )
        elif cmd[0] == "bash" and str(cmd[1]).endswith("start_crown_console.sh"):
            calls.extend(["crown_model_launcher", "launch_servants"])
            if shutil.which("nc"):
                calls.append("nc -z localhost 8000")
            else:
                calls.append("python socket_check")
            calls.append("python console_interface.py")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def fake_system(cmd):
        calls.append(cmd)
        return 0

    monkeypatch.setattr(shutil, "which", lambda *_: None)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(os, "system", fake_system)

    result = subprocess.run(["bash", str(ROOT / "start_avatar_console.sh")])

    assert result.returncode == 0
    assert "start_crown_console" in calls
    assert "python video_stream.py" in calls
    assert "wait crown stream" in calls
    wait_idx = calls.index("wait crown stream")
    assert wait_idx > calls.index("start_crown_console")
    assert wait_idx > calls.index("python video_stream.py")
    assert "python socket_check" in calls

