import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub langchain modules used by planning
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
embeddings_mod = types.ModuleType("langchain.embeddings")
class DummyEmb:
    def __init__(self, *a, **k):
        pass
embeddings_mod.HuggingFaceEmbeddings = DummyEmb
vector_mod = types.ModuleType("langchain.vectorstores")
vector_mod.FAISS = types.SimpleNamespace(
    from_texts=lambda texts, embed: types.SimpleNamespace(
        as_retriever=lambda **k: None, save_local=lambda *a: None
    ),
    load_local=lambda path, embed: types.SimpleNamespace(
        as_retriever=lambda **k: None, save_local=lambda *a: None
    ),
)
memory_mod = types.ModuleType("langchain.memory")
class DummyMemory:
    def __init__(self, retriever=None):
        self.saved = []
    def save_context(self, inp, out):
        self.saved.append((inp, out))
    def load_memory_variables(self, inp):
        return {"history": ""}
memory_mod.VectorStoreRetrieverMemory = lambda retriever=None: DummyMemory()

schema_mod = types.ModuleType("langchain.schema")
schema_mod.Document = object

sys.modules.setdefault("langchain", langchain)
sys.modules.setdefault("langchain.agents", agents_mod)
sys.modules.setdefault("langchain.chat_models", chat_mod)
sys.modules.setdefault("langchain.embeddings", embeddings_mod)
sys.modules.setdefault("langchain.vectorstores", vector_mod)
sys.modules.setdefault("langchain.memory", memory_mod)
sys.modules.setdefault("langchain.schema", schema_mod)

import importlib

planning = importlib.import_module("os_guardian.planning")


def test_plan_and_feedback(tmp_path):
    planner = planning.GuardianPlanner(memory_path=tmp_path)
    steps = planner.plan("demo instruction")
    assert steps == ["analyze_frame()", "type_text('hi')"]

    steps2 = planner.interactive_plan("next", "button")
    assert steps2 and steps2[0].startswith("click")
    assert planner.memory is not None
