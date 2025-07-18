import os
import sys
import types
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

calls = []

# Dummy pyautogui
pyautogui = types.ModuleType("pyautogui")
pyautogui.click = lambda x=0, y=0: calls.append(("click", x, y))
pyautogui.typewrite = lambda text: calls.append(("typewrite", text))
pyautogui.scroll = lambda amount: calls.append(("scroll", amount))
sys.modules["pyautogui"] = pyautogui

# Dummy selenium webdriver
class DummyDriver:
    def get(self, url):
        calls.append(("get", url))

    def execute_script(self, script):
        calls.append(("js", script))
        return "ok"

webdriver = types.SimpleNamespace(Firefox=lambda: DummyDriver())
selenium = types.ModuleType("selenium")
selenium.webdriver = webdriver
sys.modules["selenium"] = selenium
sys.modules["selenium.webdriver"] = webdriver

# Environment for safety module
os.environ["OG_POLICY"] = "allow"
os.environ["OG_ALLOWED_APPS"] = "dummy_app"

# Stub langchain just like the planning tests
class DummyAgent:
    def __init__(self):
        self.calls = []

    def run(self, text):
        self.calls.append(text)
        if "Feedback" in text:
            return "1. click(10,10)\n2. done"
        return "1. analyze_frame()\n2. type_text('hi')"

def dummy_initialize_agent(*a, **k):
    return DummyAgent()

langchain = types.ModuleType("langchain")
agents_mod = types.ModuleType("langchain.agents")
agents_mod.initialize_agent = dummy_initialize_agent
agents_mod.AgentType = types.SimpleNamespace(ZERO_SHOT_REACT_DESCRIPTION="desc")

class DummyTool:
    @classmethod
    def from_function(cls, *, name=None, func=None, description=None):
        return {"name": name, "func": func, "description": description}

agents_mod.Tool = DummyTool
chat_mod = types.ModuleType("langchain.chat_models")
chat_mod.ChatOpenAI = lambda *a, **k: object()
emb_mod = types.ModuleType("langchain.embeddings")
class DummyEmb:
    def __init__(self, *a, **k):
        pass
emb_mod.HuggingFaceEmbeddings = DummyEmb
vec_mod = types.ModuleType("langchain.vectorstores")
vec_mod.FAISS = types.SimpleNamespace(
    from_texts=lambda texts, embed: types.SimpleNamespace(
        as_retriever=lambda **k: None, save_local=lambda *a: None
    ),
    load_local=lambda path, embed: types.SimpleNamespace(
        as_retriever=lambda **k: None, save_local=lambda *a: None
    ),
)
mem_mod = types.ModuleType("langchain.memory")
class DummyMemory:
    def __init__(self, retriever=None):
        self.saved = []

    def save_context(self, inp, out):
        self.saved.append((inp, out))

    def load_memory_variables(self, inp):
        return {"history": ""}

mem_mod.VectorStoreRetrieverMemory = lambda retriever=None: DummyMemory()
schema_mod = types.ModuleType("langchain.schema")
schema_mod.Document = object
sys.modules.setdefault("langchain", langchain)
sys.modules.setdefault("langchain.agents", agents_mod)
sys.modules.setdefault("langchain.chat_models", chat_mod)
sys.modules.setdefault("langchain.embeddings", emb_mod)
sys.modules.setdefault("langchain.vectorstores", vec_mod)
sys.modules.setdefault("langchain.memory", mem_mod)
sys.modules.setdefault("langchain.schema", schema_mod)

spec = importlib.util.spec_from_file_location("os_guardian.cli", ROOT / "os_guardian" / "cli.py")
cli = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cli
assert spec.loader is not None
spec.loader.exec_module(cli)


def test_cli_open_app(monkeypatch):
    launched = []

    class DummyProc:
        def __init__(self, args):
            self.args = args
        def terminate(self):
            launched.append("terminated")

    def fake_popen(args):
        launched.append(list(args))
        return DummyProc(args)

    monkeypatch.setattr(cli.action_engine.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(cli.action_engine.safety, "confirm", lambda prompt: True)
    monkeypatch.setattr(cli.action_engine.safety, "register_undo", lambda f: None)

    cli.main(["open_app", "dummy_app"])

    assert launched == [["dummy_app"]]
