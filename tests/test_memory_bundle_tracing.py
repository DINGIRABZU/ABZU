import builtins
import importlib
import sys
from pathlib import Path

import conftest as conftest_module

conftest_module.ALLOWED_TESTS.update(
    {str(Path(__file__).resolve()), str(Path(__file__))}
)


def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.startswith("opentelemetry"):
        raise ImportError(name)
    return _real_import(name, globals, locals, fromlist, level)


_real_import = builtins.__import__


def test_memory_bundle_without_opentelemetry(monkeypatch):
    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.delitem(sys.modules, "opentelemetry", raising=False)
    monkeypatch.delitem(sys.modules, "opentelemetry.trace", raising=False)
    monkeypatch.delitem(sys.modules, "memory.bundle", raising=False)

    module = importlib.import_module("memory.bundle")
    bundle = module.MemoryBundle()

    with bundle._tracer.start_as_current_span("test") as span:
        assert span is None
