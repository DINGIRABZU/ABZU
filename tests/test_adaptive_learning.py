import builtins
import importlib
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

adaptive_learning = pytest.importorskip("INANNA_AI.adaptive_learning")
import INANNA_AI.ethical_validator as ev  # noqa: E402
import INANNA_AI.existential_reflector as er  # noqa: E402

ev = importlib.reload(ev)
er = importlib.reload(er)
EthicalValidator = ev.EthicalValidator
ExistentialReflector = er.ExistentialReflector


def test_validator_feedback_updates_threshold(monkeypatch):
    validator = EthicalValidator(allowed_users={"a"})
    old_threshold = adaptive_learning.THRESHOLD_AGENT.threshold
    try:
        validator.apply_feedback(1.0, {"extra": ["x"]})
        assert adaptive_learning.THRESHOLD_AGENT.threshold != old_threshold
        assert (
            validator.threshold == adaptive_learning.THRESHOLD_AGENT.threshold
        )  # noqa: E501
        assert "extra" in validator.categories
    finally:
        adaptive_learning.THRESHOLD_AGENT.threshold = old_threshold
        adaptive_learning.THRESHOLD_AGENT.categories.clear()


def test_reflector_feedback_updates_wording(monkeypatch):
    old_wording = list(adaptive_learning.WORDING_AGENT.wording)
    try:
        ExistentialReflector.apply_feedback(0.5, ["hello"])
        assert adaptive_learning.WORDING_AGENT.wording == ["hello"]
        assert ExistentialReflector.wording_choices == ["hello"]
    finally:
        adaptive_learning.WORDING_AGENT.wording = old_wording
        ExistentialReflector.wording_choices = old_wording or ["I am"]


def test_update_mirror_thresholds(tmp_path, monkeypatch):
    path = tmp_path / "thr.json"
    path.write_text('{"default": 0.5}')

    class DummyPPO:
        def __init__(self, *a, **k):
            pass

        def learn(self, *a, **k):
            pass

    gym_mod = types.SimpleNamespace(
        Env=object,
        spaces=types.SimpleNamespace(Box=lambda **k: None),
    )
    monkeypatch.setitem(sys.modules, "gymnasium", gym_mod)
    monkeypatch.setitem(
        sys.modules,
        "stable_baselines3",
        types.SimpleNamespace(PPO=DummyPPO),
    )
    monkeypatch.setenv("MIRROR_THRESHOLDS_PATH", str(path))

    import importlib

    al = importlib.reload(adaptive_learning)

    al.update_mirror_thresholds(1.0)
    data = json.loads(path.read_text())
    assert data["default"] > 0.5


def test_numpy_stub_permutation(monkeypatch):
    real_numpy = sys.modules.get("numpy")
    if real_numpy is not None:
        monkeypatch.delitem(sys.modules, "numpy", raising=False)
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name.startswith("numpy"):
            raise ImportError
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(
        sys.modules,
        "INANNA_AI.adaptive_learning",
        raising=False,
    )
    al = importlib.import_module("INANNA_AI.adaptive_learning")

    try:
        seq = [1, 2, 3]
        perm = al.np.random.permutation(seq)
        assert sorted(perm) == seq
        val = al.np.random.random()
        assert 0.0 <= val < 1.0
    finally:
        monkeypatch.setattr(builtins, "__import__", real_import)
        if real_numpy is not None:
            monkeypatch.setitem(sys.modules, "numpy", real_numpy)
        monkeypatch.setitem(
            sys.modules,
            "INANNA_AI.adaptive_learning",
            adaptive_learning,
        )
        importlib.reload(adaptive_learning)
