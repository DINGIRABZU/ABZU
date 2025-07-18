import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

dummy_np = types.ModuleType("numpy")
dummy_np.ndarray = object
sys.modules.setdefault("numpy", dummy_np)
dummy_scipy = types.ModuleType("scipy")
io_mod = types.ModuleType("io")
wavfile_mod = types.ModuleType("wavfile")
setattr(wavfile_mod, "write", lambda *a, **k: None)
io_mod.wavfile = wavfile_mod
dummy_scipy.io = io_mod
sys.modules.setdefault("scipy", dummy_scipy)
sys.modules.setdefault("scipy.io", io_mod)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))

from INANNA_AI.personality_layers.nigredo_layer import NigredoPersonality
from INANNA_AI.personality_layers import REGISTRY


def test_nigredo_methods_and_registry():
    layer = NigredoPersonality()
    msg = layer.speak("hello")
    assert "nigredo" in msg.lower()
    assert "hello" in msg

    path = layer.choose_path("abyss")
    assert "abyss" in path

    assert "nigredo_layer" in REGISTRY
    assert REGISTRY["nigredo_layer"] is NigredoPersonality
