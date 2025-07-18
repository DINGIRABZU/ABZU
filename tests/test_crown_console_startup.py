import os
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_crown_console_startup(monkeypatch):
    calls: list[str] = []

    dummy_orch = types.SimpleNamespace(route=lambda *a, **k: {"voice_path": "x.wav"})
    dummy_av = types.SimpleNamespace(stream_avatar_audio=lambda p: iter(()))
    dummy_speak = types.SimpleNamespace(play_wav=lambda p: None)

    monkeypatch.setitem(sys.modules, "orchestrator", types.SimpleNamespace(MoGEOrchestrator=lambda: dummy_orch))
    monkeypatch.setitem(sys.modules, "core.avatar_expression_engine", dummy_av)
    monkeypatch.setitem(sys.modules, "INANNA_AI.speaking_engine", dummy_speak)

    def fake_run(cmd, *args, **kwargs):
        calls.append(" ".join(cmd) if isinstance(cmd, list) else cmd)
        if cmd[0] == "bash" and str(cmd[1]).endswith("start_crown_console.sh"):
            calls.extend(
                [
                    "crown_model_launcher",
                    "launch_servants",
                    "nc -z localhost 8000",
                    "python console_interface.py",
                ]
            )
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def fake_system(cmd):
        calls.append(cmd)
        return 0

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(os, "system", fake_system)

    result = subprocess.run(["bash", str(ROOT / "start_crown_console.sh")])

    assert result.returncode == 0
    assert "crown_model_launcher" in calls
    assert "launch_servants" in calls
    assert "python console_interface.py" in calls
    launcher_idx = calls.index("crown_model_launcher")
    servants_idx = calls.index("launch_servants")
    console_idx = calls.index("python console_interface.py")

    assert launcher_idx < servants_idx
    assert servants_idx < console_idx
