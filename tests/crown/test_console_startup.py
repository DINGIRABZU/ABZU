"""Tests for crown console startup."""

from __future__ import annotations

__version__ = "0.0.0"

import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest
from cli import console_interface

ROOT = Path(__file__).resolve().parents[2]

SKIP = shutil.which("bash") is None or not os.access(
    ROOT / "start_crown_console.sh", os.X_OK
)


class DummySession:
    def __init__(self, prompts: list[str]):
        self._prompts = prompts

    def prompt(self, _prompt: str) -> str:
        if not self._prompts:
            raise EOFError
        return self._prompts.pop(0)


class DummyContext:
    def __enter__(self) -> "DummyContext":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.mark.skipif(SKIP, reason="requires bash and executable start_crown_console.sh")
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


def _setup_console(monkeypatch, tmp_path: Path, prompts: list[str]):
    dummy_audio = tmp_path / "reply.wav"
    dummy_audio.write_bytes(b"data")

    monkeypatch.setattr(console_interface, "_wait_for_glm_ready", lambda: object())
    monkeypatch.setattr(
        console_interface,
        "crown_prompt_orchestrator",
        lambda m, g: {"text": "ok", "emotion": "neutral"},
    )
    monkeypatch.setattr(
        console_interface,
        "PromptSession",
        lambda history=None: DummySession(prompts),
    )
    monkeypatch.setattr(console_interface, "patch_stdout", lambda: DummyContext())
    monkeypatch.setattr(console_interface.context_tracker.state, "avatar_loaded", True)
    monkeypatch.setattr(console_interface.requests, "post", lambda *a, **k: None)

    dummy_orch = types.SimpleNamespace(
        route=lambda *a, **k: {"voice_path": str(dummy_audio)}
    )
    monkeypatch.setattr(console_interface, "MoGEOrchestrator", lambda: dummy_orch)

    frames: list[bytes] = []

    def fake_stream(_path: Path):
        for f in [b"f1", b"f2"]:
            frames.append(f)
            yield f

    monkeypatch.setattr(
        console_interface.avatar_expression_engine, "stream_avatar_audio", fake_stream
    )

    audio_calls: list[str] = []
    monkeypatch.setattr(
        console_interface.speaking_engine,
        "play_wav",
        lambda p: audio_calls.append(str(p)),
    )

    log_dir = tmp_path / "logs" / "bana"
    monkeypatch.setattr(console_interface.session_logger, "AUDIO_DIR", log_dir)
    monkeypatch.setattr(console_interface.session_logger, "VIDEO_DIR", log_dir)
    monkeypatch.setattr(console_interface.session_logger, "imageio", None)
    monkeypatch.setattr(console_interface.session_logger, "np", None)

    return dummy_audio, frames, audio_calls, log_dir


def test_console_creates_bana_logs(monkeypatch, tmp_path):
    _, frames, audio_calls, log_dir = _setup_console(
        monkeypatch, tmp_path, ["hello", "/exit"]
    )

    console_interface.run_repl(["--speak"])

    files = list(log_dir.iterdir())
    assert files
    assert audio_calls
    assert frames
    assert all(re.search(r"\d{8}_\d{6}", f.name) for f in files)


def test_console_streaming_output(monkeypatch, tmp_path):
    dummy_audio, frames, audio_calls, log_dir = _setup_console(
        monkeypatch, tmp_path, ["hi", "/exit"]
    )

    console_interface.run_repl(["--speak"])

    assert audio_calls == [str(dummy_audio)]
    assert frames
    files = list(log_dir.iterdir())
    assert any(f.suffix == ".wav" for f in files)
    assert any(f.suffix != ".wav" for f in files)
