import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "perception", ROOT / "os_guardian" / "perception.py"
)
perception = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = perception
assert spec.loader is not None
spec.loader.exec_module(perception)


def test_screen_stream_uses_capture(monkeypatch):
    frame_a = object()
    frame_b = object()
    frames = [frame_a, frame_b]
    calls = []

    def fake_capture(region=None):
        if frames:
            calls.append(True)
            return frames.pop(0)
        return None

    monkeypatch.setattr(perception, "capture_screen", fake_capture)
    monkeypatch.setattr(perception.time, "sleep", lambda t: None)

    stream = perception.screen_stream(fps=2)
    f1 = next(stream)
    f2 = next(stream)

    assert calls == [True, True]
    assert f1 is frame_a
    assert f2 is frame_b


def test_analyze_frame_runs_detection_and_ocr(monkeypatch):
    class DummyFrame:
        def __getitem__(self, item):
            return f"region-{item}"

    frame = DummyFrame()

    def fake_detect(image, model_path=None):
        assert model_path == "model.pt"
        return [
            ("button", 0.9, (0, 0, 2, 2)),
            ("label", 0.8, (1, 1, 3, 3)),
        ]

    regions = []

    def fake_ocr(img):
        regions.append(img)
        return "TEXT"

    monkeypatch.setattr(perception, "detect_gui_elements", fake_detect)
    monkeypatch.setattr(perception, "extract_text", fake_ocr)

    obs = perception.analyze_frame(frame, model_path="model.pt", ocr_labels=["button"])
    assert len(obs) == 2
    assert obs[0].label == "button" and obs[0].text == "TEXT"
    assert obs[1].label == "label" and obs[1].text is None
    assert regions == ["region-(slice(0, 2, None), slice(0, 2, None))"]



