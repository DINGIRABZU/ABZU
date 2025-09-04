"""Integration tests for console streaming and Bana log creation."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Stub third-party modules to keep the test lightweight
# ---------------------------------------------------------------------------
ptk = types.ModuleType("prompt_toolkit")
ptk.PromptSession = lambda *a, **k: None
sys.modules.setdefault("prompt_toolkit", ptk)
ptk_hist = types.ModuleType("prompt_toolkit.history")
ptk_hist.FileHistory = lambda *a, **k: None
sys.modules.setdefault("prompt_toolkit.history", ptk_hist)
ptk_patch = types.ModuleType("prompt_toolkit.patch_stdout")
ptk_patch.patch_stdout = lambda: None
sys.modules.setdefault("prompt_toolkit.patch_stdout", ptk_patch)

sf_mod = types.ModuleType("soundfile")
sf_mod.write = lambda *a, **k: None
sf_mod.read = lambda *a, **k: (b"", 22050)
sys.modules.setdefault("soundfile", sf_mod)

librosa_mod = types.ModuleType("librosa")
librosa_mod.load = lambda *a, **k: ([], 22050)
librosa_mod.resample = lambda *a, **k: []
librosa_mod.effects = types.SimpleNamespace(
    pitch_shift=lambda *a, **k: [], time_stretch=lambda *a, **k: []
)
sys.modules.setdefault("librosa", librosa_mod)

opensmile_mod = types.ModuleType("opensmile")
sys.modules.setdefault("opensmile", opensmile_mod)

scipy_mod = types.ModuleType("scipy")
scipy_io_mod = types.ModuleType("scipy.io")
scipy_wav_mod = types.ModuleType("scipy.io.wavfile")
scipy_wav_mod.write = lambda *a, **k: None
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io_mod)
sys.modules.setdefault("scipy.io.wavfile", scipy_wav_mod)

sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("SPIRAL_OS.qnl_engine"))
sys.modules.setdefault(
    "SPIRAL_OS.symbolic_parser", types.ModuleType("SPIRAL_OS.symbolic_parser")
)
sys.modules.setdefault(
    "tools.reflection_loop", types.ModuleType("tools.reflection_loop")
)

gym_mod = types.ModuleType("gymnasium")
spaces_mod = types.ModuleType("spaces")


class DummyBox:
    def __init__(self, *a, **k):
        pass


spaces_mod.Box = DummyBox
gym_mod.Env = object
gym_mod.spaces = spaces_mod
sys.modules.setdefault("gymnasium", gym_mod)

sys.modules.setdefault(
    "sentence_transformers", types.ModuleType("sentence_transformers")
)

stable_mod = types.ModuleType("stable_baselines3")
stable_mod.PPO = lambda *a, **k: None
sys.modules.setdefault("stable_baselines3", stable_mod)

# Stub rag orchestrator to avoid heavy imports
rag_pkg = types.ModuleType("rag")
rag_orch = types.ModuleType("rag.orchestrator")
rag_orch.MoGEOrchestrator = lambda: None
rag_pkg.orchestrator = rag_orch
sys.modules.setdefault("rag", rag_pkg)
sys.modules.setdefault("rag.orchestrator", rag_orch)

# ---------------------------------------------------------------------------
from cli import console_interface
from tools import session_logger
from memory import narrative_engine


class DummySession:
    def __init__(self, prompts: list[str]):
        self._prompts = prompts

    def prompt(self, prompt_str: str) -> str:
        if not self._prompts:
            raise EOFError
        return self._prompts.pop(0)


class DummyContext:
    def __enter__(self) -> "DummyContext":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - trivial
        return False


@pytest.mark.skipif(False, reason="requires patched environment stubs")
def test_console_streaming_creates_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run console REPL and confirm audio/video and Bana logs are created."""
    voice = tmp_path / "out.wav"
    voice.write_bytes(b"RIFF00")

    glm = object()
    monkeypatch.setattr(console_interface, "initialize_crown", lambda: glm)

    def fake_cpo(message: str, glm_obj: object) -> dict[str, str]:
        narrative_engine.log_story("Saga")
        return {"text": "ok", "emotion": "joy"}

    monkeypatch.setattr(console_interface, "crown_prompt_orchestrator", fake_cpo)
    monkeypatch.setattr(
        console_interface,
        "PromptSession",
        lambda history=None: DummySession(["hi", "/exit"]),
    )
    monkeypatch.setattr(console_interface, "patch_stdout", lambda: DummyContext())

    frames = [[[0]]] * 2
    dummy_orch = types.SimpleNamespace(route=lambda *a, **k: {"voice_path": str(voice)})
    dummy_stream = types.SimpleNamespace(stream_avatar_audio=lambda p: iter(frames))
    dummy_reflector = types.SimpleNamespace(reflect=lambda p: {"emotion": "calm"})
    monkeypatch.setattr(console_interface, "MoGEOrchestrator", lambda: dummy_orch)
    monkeypatch.setattr(
        console_interface,
        "speaking_engine",
        types.SimpleNamespace(play_wav=lambda p: None),
    )
    monkeypatch.setitem(sys.modules, "core.avatar_expression_engine", dummy_stream)
    monkeypatch.setitem(
        sys.modules,
        "INANNA_AI.speech_loopback_reflector",
        dummy_reflector,
    )
    monkeypatch.setattr(console_interface.context_tracker.state, "avatar_loaded", True)
    monkeypatch.setattr(
        console_interface.requests, "post", lambda url, json, timeout=5: None
    )

    monkeypatch.setattr(session_logger, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(session_logger, "VIDEO_DIR", tmp_path / "video")

    def write_story(text: str) -> None:
        bana_dir = tmp_path / "logs" / "bana"
        bana_dir.mkdir(parents=True, exist_ok=True)
        (bana_dir / "story.md").write_text(text)

    monkeypatch.setattr(narrative_engine, "log_story", write_story)

    console_interface.run_repl(["--speak"])

    assert (tmp_path / "logs" / "bana" / "story.md").read_text() == "Saga"
    assert len(list((tmp_path / "audio").iterdir())) == 1
    assert len(list((tmp_path / "video").iterdir())) == 1
