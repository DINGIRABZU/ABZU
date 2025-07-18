import sys
from pathlib import Path
import types
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {"version": 1, "handlers": {}, "root": {"level": "INFO"}}
sys.modules.setdefault("yaml", yaml_mod)
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sb3_mod = types.ModuleType("stable_baselines3")
class DummyPPO:
    def __init__(self, *a, **k):
        pass

setattr(sb3_mod, "PPO", DummyPPO)
sys.modules.setdefault("stable_baselines3", sb3_mod)
gym_mod = types.ModuleType("gymnasium")
setattr(gym_mod, "Env", object)
spaces_mod = types.ModuleType("spaces")
class DummyBox:
    def __init__(self, *a, **k):
        pass

setattr(spaces_mod, "Box", DummyBox)
setattr(gym_mod, "spaces", spaces_mod)
sys.modules.setdefault("gymnasium", gym_mod)

from INANNA_AI_AGENT import INANNA_AI
import audio_ingestion
import dsp_engine
import vector_memory


def test_qnl_audio_pipeline(tmp_path, monkeypatch):
    wav = tmp_path / "song.wav"
    json_out = tmp_path / "meta.json"
    # Stub run_qnl to create files
    def fake_run_qnl(hex_input, wav=wav, json_file=json_out):
        Path(wav).write_bytes(b"\x00\x00")
        Path(json_file).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(inanna_ai, "run_qnl", fake_run_qnl)

    argv_backup = sys.argv.copy()
    sys.argv = ["INANNA_AI.py", "--hex", "012345", "--wav", str(wav), "--json", str(json_out)]
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv_backup

    monkeypatch.setattr(
        audio_ingestion.librosa,
        "load",
        lambda p, sr=44100, mono=True: (np.zeros(4), sr),
        raising=False,
    )
    data, sr = audio_ingestion.load_audio(wav, sr=22050)

    monkeypatch.setattr(dsp_engine, "_apply_ffmpeg_filter", lambda d, s, f: (d, s))
    _, sr2 = dsp_engine.pitch_shift(data, sr, 1.0)

    if vector_memory.LOG_FILE.exists():
        vector_memory.LOG_FILE.unlink()

    monkeypatch.setattr(vector_memory.qnl_utils, "quantum_embed", lambda t: np.zeros(1))
    class DummyCollection:
        def add(self, ids, embeddings, metadatas):
            pass

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    vector_memory.add_vector("test", {"sr": sr2})

    logs = vector_memory.LOG_FILE.read_text(encoding="utf-8").splitlines()
    assert logs and '"operation": "add"' in logs[-1]

