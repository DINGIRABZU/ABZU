import sys
import types
import importlib
import builtins


def test_import_without_numpy(monkeypatch):
    real_numpy = sys.modules.get("numpy")
    if real_numpy is not None:
        monkeypatch.delitem(sys.modules, "numpy", raising=False)
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "numpy":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    al = importlib.reload(importlib.import_module("INANNA_AI.adaptive_learning"))
    assert isinstance(al.np, types.SimpleNamespace)
    assert al.THRESHOLD_AGENT.model.__class__.__module__ == "INANNA_AI.adaptive_learning"

    monkeypatch.setattr(builtins, "__import__", real_import)
    if real_numpy is not None:
        monkeypatch.setitem(sys.modules, "numpy", real_numpy)
    importlib.reload(al)
