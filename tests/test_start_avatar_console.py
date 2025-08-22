from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SKIP = shutil.which("bash") is None or not os.access(
    ROOT / "start_avatar_console.sh", os.X_OK
)
pytestmark = pytest.mark.skipif(
    SKIP, reason="requires bash and executable start_avatar_console.sh"
)


def test_start_avatar_console_waits_and_fallback(monkeypatch):
    calls: list[str] = []

    def fake_run(cmd, *args, **kwargs):
        joined = " ".join(cmd) if isinstance(cmd, list) else cmd
        calls.append(joined)
        script = str(cmd[1])
        if cmd[0] == "bash" and script.endswith("start_avatar_console.sh"):
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
        elif cmd[0] == "bash" and script.endswith("start_crown_console.sh"):
            calls.extend(
                [
                    "check_requirements",
                    "crown_model_launcher",
                    "launch_servants",
                    "curl http://localhost:8000/health",
                    "python -m cli.console_interface",
                ]
            )
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def fake_system(cmd):
        calls.append(cmd)
        return 0

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
    assert "curl http://localhost:8000/health" in calls
