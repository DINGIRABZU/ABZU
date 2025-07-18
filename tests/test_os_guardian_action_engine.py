import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Create dummy pyautogui module
calls = {}

def _record(name, value):
    calls.setdefault(name, []).append(value)

pyautogui = types.ModuleType("pyautogui")
pyautogui.click = lambda x=0, y=0: _record("click", (x, y))
pyautogui.typewrite = lambda text: _record("typewrite", text)
pyautogui.scroll = lambda amount: _record("scroll", amount)
sys.modules["pyautogui"] = pyautogui

# Create dummy selenium webdriver module
class DummyDriver:
    def get(self, url):
        _record("get", url)

    def execute_script(self, script):
        _record("js", script)
        return "result"

webdriver = types.SimpleNamespace(Firefox=lambda: DummyDriver())
selenium = types.ModuleType("selenium")
selenium.webdriver = webdriver
sys.modules["selenium"] = selenium
sys.modules["selenium.webdriver"] = webdriver

import importlib.util

spec = importlib.util.spec_from_file_location(
    "os_guardian.action_engine", ROOT / "os_guardian" / "action_engine.py"
)
action_engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = action_engine
assert spec.loader is not None
spec.loader.exec_module(action_engine)


def test_mouse_and_keyboard_actions():
    calls.clear()
    action_engine.click(1, 2)
    action_engine.type_text("hi")
    action_engine.scroll(-5)
    assert calls["click"] == [(1, 2)]
    assert calls["typewrite"] == ["hi"]
    assert calls["scroll"] == [-5]


def test_run_command_whitelist(monkeypatch):
    recorded = []

    def fake_run(args, capture_output=True, text=True, check=False):
        recorded.append(list(args))
        class CP:
            def __init__(self):
                self.args = args
                self.stdout = "ok"
        return CP()

    monkeypatch.setattr(action_engine.subprocess, "run", fake_run)
    res = action_engine.run_command(["echo", "hello"])
    assert recorded == [["echo", "hello"]]
    assert res.stdout == "ok"
    res = action_engine.run_command("rm -rf /")
    assert res is None
    assert recorded == [["echo", "hello"]]


def test_open_url_and_js():
    calls.clear()
    drv = action_engine.open_url("http://example.com")
    assert isinstance(drv, DummyDriver)
    assert calls["get"] == ["http://example.com"]
    out = action_engine.run_js("return 1;", drv)
    assert out == "result"
    assert calls["js"] == ["return 1;"]
