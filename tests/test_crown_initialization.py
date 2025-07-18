import sys
from types import ModuleType
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import logging
import types

yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)

dummy_np = types.ModuleType("numpy")
dummy_np.ndarray = object
dummy_np.zeros = lambda *a, **k: None
dummy_np.pi = 3.14159
dummy_np.float32 = float
sys.modules.setdefault("numpy", dummy_np)

ptk_mod = types.ModuleType("prompt_toolkit")
ptk_mod.PromptSession = lambda *a, **k: None
sys.modules.setdefault("prompt_toolkit", ptk_mod)
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
librosa_mod.effects = types.SimpleNamespace(pitch_shift=lambda *a, **k: [], time_stretch=lambda *a, **k: [])
sys.modules.setdefault("librosa", librosa_mod)

opensmile_mod = types.ModuleType("opensmile")
sys.modules.setdefault("opensmile", opensmile_mod)

scipy_mod = types.ModuleType("scipy")
scipy_io_mod = types.ModuleType("scipy.io")
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io_mod)
scipy_wavfile_mod = types.ModuleType("scipy.io.wavfile")
scipy_wavfile_mod.write = lambda *a, **k: None
sys.modules.setdefault("scipy.io.wavfile", scipy_wavfile_mod)

sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("SPIRAL_OS.qnl_engine"))
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", types.ModuleType("SPIRAL_OS.symbolic_parser"))

stable_mod = types.ModuleType("stable_baselines3")
class DummyPPO:
    def __init__(self, *a, **k):
        pass
stable_mod.PPO = DummyPPO
sys.modules.setdefault("stable_baselines3", stable_mod)

gym_mod = types.ModuleType("gymnasium")
gym_mod.Env = object
spaces_mod = types.ModuleType("spaces")
class DummyBox:
    def __init__(self, *a, **k):
        pass
spaces_mod.Box = DummyBox
gym_mod.spaces = spaces_mod
sys.modules.setdefault("gymnasium", gym_mod)

yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
import pytest
import init_crown_agent
import console_interface
import INANNA_AI.glm_integration as gi


class DummyResponse:
    def __init__(self, text: str) -> None:
        self._text = text
        self.text = text

    def json(self):
        return {"text": self._text}

    def raise_for_status(self):
        return None


class DummySession:
    def __init__(self, prompts: list[str]):
        self._prompts = prompts

    def prompt(self, prompt_str: str):
        if not self._prompts:
            raise EOFError
        return self._prompts.pop(0)


class DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_initialize_crown(monkeypatch, tmp_path, caplog):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("glm_api_url: http://file\n", encoding="utf-8")

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_init_servants", lambda c: None)
    monkeypatch.setattr(init_crown_agent, "_check_glm", lambda i: None)
    monkeypatch.setattr(init_crown_agent.vector_memory, "_get_collection", lambda: None)
    monkeypatch.setattr(init_crown_agent.corpus_memory, "create_collection", lambda dir_path=None: None)

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: DummyResponse("pong")
    dummy.RequestException = Exception
    monkeypatch.setattr(gi, "requests", dummy)

    monkeypatch.setenv("GLM_API_URL", "http://env")
    monkeypatch.setenv("GLM_API_KEY", "secret")

    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))

    with caplog.at_level(logging.INFO):
        client = init_crown_agent.initialize_crown()
    assert isinstance(client, gi.GLMIntegration)
    assert client.endpoint == "http://env"
    assert client.headers == {"Authorization": "Bearer secret"}
    assert client.complete("hi") == "pong"
    assert any("GLM_API_URL" in r.message for r in caplog.records)
    assert any("initializing vector memory" in r.message for r in caplog.records)


def test_initialize_crown_glm_error(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("", encoding="utf-8")

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_init_servants", lambda c: None)
    monkeypatch.setattr(init_crown_agent.vector_memory, "_get_collection", lambda: None)
    monkeypatch.setattr(init_crown_agent.corpus_memory, "create_collection", lambda dir_path=None: None)

    def fail_check(i):
        raise RuntimeError("bad")

    monkeypatch.setattr(init_crown_agent, "_check_glm", fail_check)

    with pytest.raises(SystemExit):
        init_crown_agent.initialize_crown()


def test_console_flow(monkeypatch, capsys):
    calls = {}

    def dummy_orchestrator(msg, glm):
        calls["msg"] = msg
        calls["glm"] = glm
        return "reply"

    glm = object()

    monkeypatch.setattr(console_interface, "initialize_crown", lambda: glm)
    monkeypatch.setattr(console_interface, "crown_prompt_orchestrator", dummy_orchestrator)
    monkeypatch.setattr(console_interface, "PromptSession", lambda history=None: DummySession(["hello", "/exit"]))
    monkeypatch.setattr(console_interface, "patch_stdout", lambda: DummyContext())

    console_interface.run_repl([])
    out = capsys.readouterr().out
    assert "reply" in out
    assert calls == {"msg": "hello", "glm": glm}


def test_console_speak(monkeypatch, capsys):
    calls = {}

    def dummy_orchestrator(msg, glm):
        calls["msg"] = msg
        calls["glm"] = glm
        return {"text": "ok", "emotion": "joy"}

    glm = object()

    monkeypatch.setattr(console_interface, "initialize_crown", lambda: glm)
    monkeypatch.setattr(console_interface, "crown_prompt_orchestrator", dummy_orchestrator)
    monkeypatch.setattr(console_interface, "PromptSession", lambda history=None: DummySession(["hello", "/exit"]))
    monkeypatch.setattr(console_interface, "patch_stdout", lambda: DummyContext())

    dummy_orch = types.SimpleNamespace(route=lambda *a, **k: {"voice_path": "out.wav"})
    dummy_reflector = types.SimpleNamespace(reflect=lambda p: calls.setdefault("reflect", p))
    dummy_stream = types.SimpleNamespace(stream_avatar_audio=lambda p: iter(()))

    monkeypatch.setattr(console_interface, "MoGEOrchestrator", lambda: dummy_orch)
    monkeypatch.setattr(console_interface, "speaking_engine", types.SimpleNamespace(play_wav=lambda p: calls.setdefault("play", p)))
    monkeypatch.setitem(sys.modules, "core.avatar_expression_engine", dummy_stream)
    monkeypatch.setitem(sys.modules, "INANNA_AI.speech_loopback_reflector", dummy_reflector)

    console_interface.run_repl(["--speak"])
    out = capsys.readouterr().out
    assert "ok" in out
    assert calls["play"] == "out.wav"
    assert calls["reflect"] == "out.wav"
