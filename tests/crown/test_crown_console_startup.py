"""Tests for crown console startup."""

from __future__ import annotations

__version__ = "0.0.0"

import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

SKIP = shutil.which("bash") is None or not os.access(
    ROOT / "start_crown_console.sh", os.X_OK
)
pytestmark = pytest.mark.skipif(
    SKIP, reason="requires bash and executable start_crown_console.sh"
)


def test_crown_console_startup(monkeypatch):
    calls: list[str] = []

    dummy_orch = types.SimpleNamespace(
        route=lambda *a, **k: {"voice_path": "x.wav"},
    )
    dummy_av = types.SimpleNamespace(stream_avatar_audio=lambda p: iter(()))
    dummy_speak = types.SimpleNamespace(play_wav=lambda p: None)

    rag_pkg = types.ModuleType("rag")
    monkeypatch.setitem(sys.modules, "rag", rag_pkg)
    orch_ns = types.SimpleNamespace(MoGEOrchestrator=lambda: dummy_orch)
    rag_pkg.orchestrator = orch_ns
    monkeypatch.setitem(sys.modules, "rag.orchestrator", orch_ns)
    monkeypatch.setitem(sys.modules, "core.avatar_expression_engine", dummy_av)
    monkeypatch.setitem(sys.modules, "INANNA_AI.speaking_engine", dummy_speak)

    def fake_run(cmd, *args, **kwargs):
        calls.append(" ".join(cmd) if isinstance(cmd, list) else cmd)
        script = str(cmd[1])
        if cmd[0] == "bash" and script.endswith("start_crown_console.sh"):
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

    result = subprocess.run(["bash", str(ROOT / "start_crown_console.sh")])

    assert result.returncode == 0
    assert "check_requirements" in calls
    assert "crown_model_launcher" in calls
    assert "launch_servants" in calls
    assert "curl http://localhost:8000/health" in calls
    assert "python -m cli.console_interface" in calls
    launcher_idx = calls.index("crown_model_launcher")
    servants_idx = calls.index("launch_servants")
    console_idx = calls.index("python -m cli.console_interface")

    assert launcher_idx < servants_idx
    assert servants_idx < console_idx
