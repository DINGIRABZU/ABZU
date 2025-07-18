import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]


def test_python_crown_console(monkeypatch):
    calls: list[str] = []

    module_path = ROOT / "start_crown_console.py"
    loader = SourceFileLoader("start_crown_console", str(module_path))
    spec = importlib.util.spec_from_loader("start_crown_console", loader)
    mod = importlib.util.module_from_spec(spec)
    dummy_dotenv = types.SimpleNamespace(load_dotenv=lambda *_: None)
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)
    loader.exec_module(mod)

    def fake_sleep(_):
        # Simulate one loop iteration
        for p in procs:
            polls[p] = 0

    polls: dict[object, int] = {}
    procs: list[object] = []

    class DummyProc:
        def __init__(self, args: list[str]):
            self.args = args
            procs.append(self)
            polls[self] = None
            calls.append(" ".join(args))

        def poll(self):
            return polls[self]

        def terminate(self):
            calls.append(f"term {' '.join(self.args)}")

        def wait(self, timeout=None):
            calls.append(f"wait {' '.join(self.args)}")

    def fake_popen(args, *a, **k):
        return DummyProc(args)

    dummy_dotenv = types.SimpleNamespace(load_dotenv=lambda *_: None)
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)
    monkeypatch.setattr(mod.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(mod, "load_dotenv", dummy_dotenv.load_dotenv)
    monkeypatch.setattr(mod.time, "sleep", fake_sleep)

    mod.main()

    assert f"bash {ROOT / 'start_crown_console.sh'}" in calls[0]
    assert sys.executable in calls[1]
    assert str(ROOT / "video_stream.py") in calls[1]
    assert any(c.startswith("wait ") for c in calls)
