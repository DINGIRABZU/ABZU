import sys
from pathlib import Path
import importlib
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import db_storage


def test_rl_metrics_module(monkeypatch):
    class DummyPPO:
        def __init__(self, *a, **k):
            pass
        def learn(self, *a, **k):
            pass
    monkeypatch.setitem(sys.modules, "stable_baselines3", types.SimpleNamespace(PPO=DummyPPO))
    class DummyBox:
        def __init__(self, *a, **k):
            pass

    dummy_gym = types.SimpleNamespace(
        Env=type("Env", (), {}),
        spaces=types.SimpleNamespace(Box=DummyBox),
    )
    monkeypatch.setitem(sys.modules, "gymnasium", dummy_gym)

    dummy_streamlit = types.SimpleNamespace(
        set_page_config=lambda **k: None,
        title=lambda x: None,
        line_chart=lambda x: None,
        write=lambda x: None,
        subheader=lambda x: None,
        markdown=lambda x: None,
    )
    monkeypatch.setitem(sys.modules, "streamlit", dummy_streamlit)

    monkeypatch.setattr(
        db_storage,
        "fetch_feedback",
        lambda limit=None: [
            {
                "timestamp": "2024-01-01T00:00:00",
                "emotion": "calm",
                "satisfaction": 0.9,
                "ethical_alignment": 0.8,
                "existential_clarity": 1.0,
            }
        ],
    )

    mod = importlib.import_module("dashboard.rl_metrics")
    assert mod is not None

