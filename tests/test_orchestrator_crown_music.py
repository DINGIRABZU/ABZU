import sys
from pathlib import Path
import types
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub optional dependencies
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
sf_mod = sys.modules["soundfile"]
setattr(sf_mod, "write", lambda path, data, sr, subtype=None: Path(path).touch())
scipy_mod = types.ModuleType("scipy")
scipy_io = types.ModuleType("scipy.io")
wavfile_mod = types.ModuleType("scipy.io.wavfile")
wavfile_mod.write = lambda *a, **k: None
scipy_io.wavfile = wavfile_mod
signal_mod = types.ModuleType("scipy.signal")
signal_mod.butter = lambda *a, **k: (None, None)
signal_mod.lfilter = lambda *a, **k: []
scipy_mod.signal = signal_mod
scipy_mod.io = scipy_io
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io)
sys.modules.setdefault("scipy.signal", signal_mod)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
qnl_stub = types.ModuleType("qnl_engine")
qnl_stub.hex_to_song = lambda *a, **k: ([], np.zeros(1, dtype=np.int16))
sys.modules.setdefault("SPIRAL_OS.qnl_engine", qnl_stub)
sym_stub = types.ModuleType("symbolic_parser")
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", sym_stub)
sp_mod = sys.modules["SPIRAL_OS"]
setattr(sp_mod, "qnl_engine", qnl_stub)
setattr(sp_mod, "symbolic_parser", sym_stub)

import orchestrator
from orchestrator import MoGEOrchestrator


def test_crown_music_path(monkeypatch, tmp_path):
    orch = MoGEOrchestrator()
    info = {"emotion": "joy"}

    monkeypatch.setattr(
        "INANNA_AI.corpus_memory.search_corpus",
        lambda *a, **k: [("p", "s")],
    )
    monkeypatch.setattr(orchestrator.vector_memory, "add_vector", lambda *a, **k: None)

    dummy_wave = np.zeros(10, dtype=np.int16)
    monkeypatch.setattr(
        "SPIRAL_OS.qnl_engine.hex_to_song",
        lambda x, duration_per_byte=1.0: ([{"phrase": "p"}], dummy_wave),
    )
    written = {}

    def fake_write(path, wave, sr):
        written["path"] = path
        written["wave"] = wave
        written["sr"] = sr

    monkeypatch.setattr(orchestrator.sf, "write", fake_write)

    res = orch.route(
        "hello",
        info,
        text_modality=False,
        voice_modality=False,
        music_modality=True,
    )

    assert res["music_path"] == str(written["path"])
    assert res["qnl_phrases"] == [{"phrase": "p"}]

