import builtins
import importlib
import sys
import types


def test_import_without_numpy(monkeypatch):
    real_numpy = sys.modules.get("numpy")
    if real_numpy is not None:
        monkeypatch.delitem(sys.modules, "numpy", raising=False)
    monkeypatch.delitem(sys.modules, "stable_baselines3", raising=False)
    monkeypatch.delitem(sys.modules, "gymnasium", raising=False)
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith(("numpy", "stable_baselines3", "gymnasium")):
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    mod = "INANNA_AI.adaptive_learning"
    monkeypatch.delitem(sys.modules, mod, raising=False)
    al = importlib.import_module(mod)
    assert isinstance(al.np, types.SimpleNamespace)
    module = al.THRESHOLD_AGENT.model.__class__.__module__
    assert "stable_baselines3" not in module

    monkeypatch.setattr(builtins, "__import__", real_import)
    if real_numpy is not None:
        monkeypatch.setitem(sys.modules, "numpy", real_numpy)
    importlib.reload(al)
