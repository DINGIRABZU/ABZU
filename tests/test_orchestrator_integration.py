from __future__ import annotations

import sys
import types
from pathlib import Path

from tests.helpers import emotion_stub
from tests.helpers.config_stub import build_settings


def setup_module(module):
    pkg = types.ModuleType("INANNA_AI")
    sys.modules["INANNA_AI"] = pkg

    class DummyResponder:
        def generate_reply(self, text, emotion_data):
            return "ok"

    response_manager = types.ModuleType("response_manager")
    response_manager.ResponseManager = lambda: DummyResponder()
    pkg.response_manager = response_manager
    sys.modules["INANNA_AI.response_manager"] = response_manager

    pkg.emotion_analysis = emotion_stub
    sys.modules["INANNA_AI.emotion_analysis"] = emotion_stub

    personality_layers = types.ModuleType("personality_layers")

    class AlbedoPersonality:
        def generate_response(self, text):
            return "persona"

    personality_layers.AlbedoPersonality = AlbedoPersonality
    personality_layers.REGISTRY = {}
    pkg.personality_layers = personality_layers
    sys.modules["INANNA_AI.personality_layers"] = personality_layers

    voice_layer_albedo = types.ModuleType("voice_layer_albedo")
    pkg.voice_layer_albedo = voice_layer_albedo
    sys.modules["INANNA_AI.voice_layer_albedo"] = voice_layer_albedo

    tts_coqui = types.ModuleType("tts_coqui")
    tts_coqui.synthesize_speech = lambda text, emotion: "path"
    pkg.tts_coqui = tts_coqui
    sys.modules["INANNA_AI.tts_coqui"] = tts_coqui

    listening_engine = types.ModuleType("listening_engine")
    listening_engine.analyze_audio = lambda duration: (None, {})
    pkg.listening_engine = listening_engine
    sys.modules["INANNA_AI.listening_engine"] = listening_engine

    db_storage = types.ModuleType("db_storage")
    db_storage.DB_PATH = Path("/tmp/test.db")
    db_storage.init_db = lambda path: None
    db_storage.log_benchmark = lambda *a, **k: None
    pkg.db_storage = db_storage
    sys.modules["INANNA_AI.db_storage"] = db_storage

    sys.modules["crown_decider"] = types.SimpleNamespace(
        decide_expression_options=lambda e: {}
    )
    sys.modules["voice_aura"] = types.ModuleType("voice_aura")

    spiral_pkg = types.ModuleType("SPIRAL_OS")
    qnl_engine = types.ModuleType("qnl_engine")
    qnl_engine.parse_input = lambda text: {"tone": "neutral"}
    symbolic_parser = types.ModuleType("symbolic_parser")
    symbolic_parser.parse_intent = lambda data: []
    symbolic_parser._INTENTS = {}
    symbolic_parser._gather_text = lambda data: ""
    spiral_pkg.qnl_engine = qnl_engine
    spiral_pkg.symbolic_parser = symbolic_parser
    sys.modules["SPIRAL_OS"] = spiral_pkg
    sys.modules["SPIRAL_OS.qnl_engine"] = qnl_engine
    sys.modules["SPIRAL_OS.symbolic_parser"] = symbolic_parser

    invocation_engine = types.ModuleType("invocation_engine")
    invocation_engine._extract_symbols = lambda text: text
    invocation_engine.invoke = lambda *a, **k: []
    invocation_engine.invoke_ritual = lambda name: []
    sys.modules["invocation_engine"] = invocation_engine

    emotional_state = types.ModuleType("emotional_state")
    emotional_state.get_current_layer = lambda: None
    emotional_state.set_current_layer = lambda layer: None
    emotional_state.get_last_emotion = lambda: "neutral"
    emotional_state.set_last_emotion = lambda e: None
    emotional_state.set_resonance_level = lambda v: None
    sys.modules["emotional_state"] = emotional_state

    training_guide = types.ModuleType("training_guide")
    training_guide.log_result = lambda *a, **k: None
    sys.modules["training_guide"] = training_guide

    insight_compiler = types.ModuleType("insight_compiler")
    insight_compiler.update_insights = lambda *a, **k: None
    insight_compiler.load_insights = lambda: {}
    sys.modules["insight_compiler"] = insight_compiler

    learning_mutator = types.ModuleType("learning_mutator")
    learning_mutator.propose_mutations = lambda insights: []
    sys.modules["learning_mutator"] = learning_mutator

    tools_pkg = types.ModuleType("tools")
    reflection_loop = types.ModuleType("reflection_loop")
    reflection_loop.load_thresholds = lambda: {"default": 1.0}
    reflection_loop.run_reflection_loop = lambda iterations=1: None
    tools_pkg.reflection_loop = reflection_loop
    sys.modules["tools"] = tools_pkg
    sys.modules["tools.reflection_loop"] = reflection_loop

    vector_memory = types.ModuleType("vector_memory")
    vector_memory.query_vectors = lambda **kw: []
    vector_memory.add_vector = lambda *a, **k: None
    sys.modules["vector_memory"] = vector_memory

    archetype_shift_engine = types.ModuleType("archetype_shift_engine")
    archetype_shift_engine.EMOTION_LAYER_MAP = {}
    sys.modules["archetype_shift_engine"] = archetype_shift_engine

    config_mod = types.ModuleType("config")
    config_mod.settings = build_settings()
    config_mod.reload = lambda: None
    sys.modules.setdefault("config", config_mod)


def test_orchestrator_integration():
    from core.emotion_analyzer import EmotionAnalyzer
    from core.memory_logger import MemoryLogger
    from core.model_selector import ModelSelector
    from core.task_profiler import TaskProfiler
    from rag.orchestrator import MoGEOrchestrator

    class StubTaskProfiler(TaskProfiler):
        def __init__(self):
            super().__init__(ritual_profile={})
            self.seen: list[str] = []

        def classify(self, text):
            self.seen.append(text)
            return "technical"

    tp = StubTaskProfiler()
    ea = EmotionAnalyzer()
    ms = ModelSelector()
    ml = MemoryLogger()

    orch = MoGEOrchestrator(
        emotion_analyzer=ea,
        model_selector=ms,
        memory_logger=ml,
        task_profiler=tp,
    )

    res = orch.route(
        "hello",
        {"emotion": "neutral", "archetype": "hero", "weight": 0.5},
    )

    assert tp.seen == ["hello"]
    assert res["model"] in {"glm", "deepseek", "mistral"}
