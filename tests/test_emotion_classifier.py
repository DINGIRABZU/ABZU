import sys
from pathlib import Path
import types
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

from ml import emotion_classifier as ec


def test_train_and_predict(tmp_path, monkeypatch):
    model_path = tmp_path / "model.joblib"
    monkeypatch.setattr(ec, "MODEL_PATH", model_path)

    X = np.array([
        [100.0, 80.0],
        [350.0, 130.0],
        [200.0, 100.0],
    ])
    y = np.array(["calm", "stress", "neutral"])

    ec.train_from_arrays(X, y)
    assert model_path.exists()

    ec._MODEL = None
    pred = ec.predict_emotion({"pitch": 350.0, "tempo": 130.0})
    assert pred == "stress"

