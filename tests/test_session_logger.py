import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ptk_mod = types.ModuleType("prompt_toolkit")
ptk_mod.PromptSession = lambda *a, **k: None
sys.modules.setdefault("prompt_toolkit", ptk_mod)
ptk_hist = types.ModuleType("prompt_toolkit.history")
ptk_hist.FileHistory = lambda *a, **k: None
sys.modules.setdefault("prompt_toolkit.history", ptk_hist)
ptk_patch = types.ModuleType("prompt_toolkit.patch_stdout")
ptk_patch.patch_stdout = lambda: None
sys.modules.setdefault("prompt_toolkit.patch_stdout", ptk_patch)

yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)

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
sys.modules.setdefault("tools.reflection_loop", types.ModuleType("tools.reflection_loop"))

gym_mod = types.ModuleType("gymnasium")
gym_mod.Env = object
spaces_mod = types.ModuleType("spaces")
class DummyBox:
    def __init__(self, *a, **k):
        pass
spaces_mod.Box = DummyBox
gym_mod.spaces = spaces_mod
sys.modules.setdefault("gymnasium", gym_mod)

sent_mod = types.ModuleType("sentence_transformers")
sys.modules.setdefault("sentence_transformers", sent_mod)

stable_mod = types.ModuleType("stable_baselines3")
class DummyPPO:
    def __init__(self, *a, **k):
        pass
stable_mod.PPO = DummyPPO
sys.modules.setdefault("stable_baselines3", stable_mod)

dummy_np = types.ModuleType("numpy")
dummy_np.ndarray = object
dummy_np.zeros = lambda *a, **k: None
dummy_np.pi = 3.14159
dummy_np.float32 = float
sys.modules.setdefault("numpy", dummy_np)

import console_interface
from tools import session_logger


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


def test_logging_files_created(tmp_path, monkeypatch):
    voice = tmp_path / "out.wav"
    voice.write_bytes(b"RIFF00")

    glm = object()
    monkeypatch.setattr(console_interface, "initialize_crown", lambda: glm)
    monkeypatch.setattr(console_interface, "crown_prompt_orchestrator", lambda m, g: {"text": "ok", "emotion": "joy"})
    monkeypatch.setattr(console_interface, "PromptSession", lambda history=None: DummySession(["hi", "/exit"]))
    monkeypatch.setattr(console_interface, "patch_stdout", lambda: DummyContext())

    frames = [[[0]]] * 2
    dummy_orch = types.SimpleNamespace(route=lambda *a, **k: {"voice_path": str(voice)})
    dummy_stream = types.SimpleNamespace(stream_avatar_audio=lambda p: iter(frames))
    dummy_reflector = types.SimpleNamespace(reflect=lambda p: {"emotion": "calm"})

    monkeypatch.setattr(console_interface, "MoGEOrchestrator", lambda: dummy_orch)
    monkeypatch.setattr(console_interface, "speaking_engine", types.SimpleNamespace(play_wav=lambda p: None))
    monkeypatch.setitem(sys.modules, "core.avatar_expression_engine", dummy_stream)
    monkeypatch.setitem(sys.modules, "INANNA_AI.speech_loopback_reflector", dummy_reflector)
    monkeypatch.setattr(console_interface.context_tracker.state, "avatar_loaded", True)

    monkeypatch.setattr(session_logger, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(session_logger, "VIDEO_DIR", tmp_path / "video")

    console_interface.run_repl(["--speak"])

    assert len(list((tmp_path / "audio").iterdir())) == 1
    assert len(list((tmp_path / "video").iterdir())) == 1
