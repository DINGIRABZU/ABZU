import sys
from pathlib import Path
import types
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))

import play_ritual_music as prm



def test_play_ritual_music_cli(tmp_path, monkeypatch):
    def dummy_compose(tempo, melody, *, sample_rate=44100, wav_path=None, wave_type="sine"):
        wave = np.zeros(100, dtype=np.float32)
        if wav_path:
            sf.write(wav_path, wave, sample_rate)
        return wave

    monkeypatch.setattr(prm.layer_generators, "compose_human_layer", dummy_compose)
    monkeypatch.setattr(prm.expressive_output, "play_audio", lambda p, loop=False: None)

    out = tmp_path / "ritual.wav"
    prm.main(["--emotion", "joy", "--ritual", "\u2609", "--output", str(out)])

    assert out.exists()
