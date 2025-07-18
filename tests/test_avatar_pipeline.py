import sys
import types
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import video_engine, avatar_expression_engine, context_tracker
import emotional_state


def test_sadtalker_pipeline(monkeypatch):
    class Dummy:
        def generate(self, path):
            return [np.full((1, 1, 3), 123, dtype=np.uint8)]

    monkeypatch.setattr(video_engine, "SadTalkerPipeline", Dummy)
    monkeypatch.setattr(video_engine, "Wav2LipPredictor", None)
    stream = video_engine.start_stream(lip_sync_audio=Path("x.wav"))
    frame = next(stream)
    assert frame[0, 0, 0] == 123


def test_controlnet_gesture(monkeypatch):
    def apply_gesture(frame):
        frame[0, 0] = [99, 99, 99]
        return frame

    ctrl = types.SimpleNamespace(apply_gesture=apply_gesture)
    monkeypatch.setattr(video_engine, "controlnet", ctrl)
    monkeypatch.setattr(context_tracker.state, "avatar_loaded", False)
    stream = video_engine.start_stream()
    frame = next(stream)
    assert (frame[0, 0] == np.array([99, 99, 99])).all()


def test_load_traits_with_skins(tmp_path, monkeypatch):
    cfg = tmp_path / "cfg.toml"
    cfg.write_text(
        """eye_color=[1,2,3]\nsigil='x'\n[skins]\nalbedo_layer='skin.png'"""
    )
    monkeypatch.setattr(video_engine, "_CONFIG_PATH", cfg)
    traits = video_engine._load_traits()
    assert traits.skins["albedo_layer"] == "skin.png"

