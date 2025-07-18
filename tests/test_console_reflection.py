import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import console_interface
import emotional_state


class DummySession:
    def __init__(self, prompts):
        self._prompts = prompts

    def prompt(self, prompt_str):
        if not self._prompts:
            raise EOFError
        return self._prompts.pop(0)


class DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_console_reflection_updates_state(monkeypatch):
    glm = object()
    monkeypatch.setattr(console_interface, "initialize_crown", lambda: glm)
    monkeypatch.setattr(console_interface, "crown_prompt_orchestrator", lambda m, g: {"text": "ok", "emotion": "joy"})
    monkeypatch.setattr(console_interface, "PromptSession", lambda history=None: DummySession(["hi", "/exit"]))
    monkeypatch.setattr(console_interface, "patch_stdout", lambda: DummyContext())

    dummy_orch = types.SimpleNamespace(route=lambda *a, **k: {"voice_path": "out.wav"})
    dummy_reflector = types.SimpleNamespace(reflect=lambda p: {"emotion": "calm"})
    dummy_stream = types.SimpleNamespace(stream_avatar_audio=lambda p: iter(()))

    monkeypatch.setattr(console_interface, "MoGEOrchestrator", lambda: dummy_orch)
    monkeypatch.setattr(console_interface, "speaking_engine", types.SimpleNamespace(play_wav=lambda p: None))
    monkeypatch.setitem(sys.modules, "core.avatar_expression_engine", dummy_stream)
    monkeypatch.setitem(sys.modules, "INANNA_AI.speech_loopback_reflector", dummy_reflector)

    captured = {}

    def fake_set(emotion):
        captured["emotion"] = emotion

    monkeypatch.setattr(emotional_state, "set_last_emotion", fake_set)

    console_interface.run_repl(["--speak"])

    assert captured["emotion"] == "calm"
