import re
import sys
import types
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from prometheus_fastapi_instrumentator import Instrumentator

# Stub heavy dependencies before importing server
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))
sys.modules.setdefault("core", ModuleType("core"))
video_engine_stub = ModuleType("video_engine")
video_engine_stub.start_stream = lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
feedback_logging_stub = ModuleType("feedback_logging")
feedback_logging_stub.append_feedback = lambda *a, **k: None
core_mod = sys.modules["core"]
core_mod.video_engine = video_engine_stub
core_mod.feedback_logging = feedback_logging_stub
sys.modules.setdefault("core.video_engine", video_engine_stub)
sys.modules.setdefault("core.feedback_logging", feedback_logging_stub)
core_utils_stub = ModuleType("core.utils")
optional_deps_stub = ModuleType("optional_deps")
optional_deps_stub.lazy_import = lambda name: SimpleNamespace(__stub__=True)
core_utils_stub.optional_deps = optional_deps_stub
sys.modules.setdefault("core.utils", core_utils_stub)
sys.modules.setdefault("core.utils.optional_deps", optional_deps_stub)

video_stream_stub = ModuleType("video_stream")
video_stream_stub.router = APIRouter()


async def _close_vs(*a, **k):
    pass


video_stream_stub.close_peers = _close_vs
video_stream_stub.start_stream = lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)])
sys.modules.setdefault("video_stream", video_stream_stub)

connectors_mod = ModuleType("connectors")
webrtc_stub = ModuleType("webrtc_connector")
webrtc_stub.router = APIRouter()
webrtc_stub.start_call = lambda *a, **k: None


async def _close_wc(*a, **k):
    pass


webrtc_stub.close_peers = _close_wc
connectors_mod.webrtc_connector = webrtc_stub
sys.modules.setdefault("connectors", connectors_mod)
sys.modules.setdefault("connectors.webrtc_connector", webrtc_stub)

inanna_mod = ModuleType("INANNA_AI.glm_integration")
inanna_mod.GLMIntegration = lambda *a, **k: None
sys.modules.setdefault("INANNA_AI.glm_integration", inanna_mod)

corpus_memory_logging_stub = ModuleType("corpus_memory_logging")
corpus_memory_logging_stub.log_interaction = lambda *a, **k: None
corpus_memory_logging_stub.load_interactions = lambda *a, **k: []
corpus_memory_logging_stub.log_ritual_result = lambda *a, **k: None
sys.modules.setdefault("corpus_memory_logging", corpus_memory_logging_stub)

music_generation_stub = ModuleType("music_generation")
music_generation_stub.generate_from_text = lambda *a, **k: Path("song.wav")
music_generation_stub.OUTPUT_DIR = Path(".")
sys.modules.setdefault("music_generation", music_generation_stub)

crown_mod = ModuleType("crown_prompt_orchestrator")
crown_mod.crown_prompt_orchestrator = lambda msg, glm: {"model": "stub"}


async def _cpo_async(msg, glm):
    return {"model": "stub"}


crown_mod.crown_prompt_orchestrator_async = _cpo_async
sys.modules.setdefault("crown_prompt_orchestrator", crown_mod)

guardian_stub = ModuleType("agents.guardian")
guardian_stub.run_validated_task = lambda *a, **k: None
sys.modules.setdefault("agents.guardian", guardian_stub)

import server
import narrative_api
from prometheus_client import REGISTRY

# Ensure real init_crown_agent module is loaded for metrics test
if "servant_health_status" in REGISTRY._names_to_collectors:
    REGISTRY.unregister(REGISTRY._names_to_collectors["servant_health_status"])
if "init_crown_agent" in sys.modules:
    del sys.modules["init_crown_agent"]
import init_crown_agent


def test_boot_duration_metric_exposed():
    with TestClient(server.app) as client:
        resp = client.get("/metrics")
    match = re.search(
        r'service_boot_duration_seconds\{service="core"\} ([0-9.]+)', resp.text
    )
    assert match is not None
    assert float(match.group(1)) >= 0.0


def test_narrative_throughput_metric_exposed():
    app = FastAPI()
    app.include_router(narrative_api.router)
    Instrumentator().instrument(app).expose(app)
    with TestClient(app) as client:
        client.post("/story", json={"text": "hello"})
        resp = client.get("/metrics")
    assert "narrative_events_total" in resp.text


def test_servant_health_metric_exposed(monkeypatch):
    app = FastAPI()
    Instrumentator().instrument(app).expose(app)

    class DummyResp:
        status_code = 200

        def raise_for_status(self):
            return None

    def fake_get(url, timeout=5):
        return DummyResp()

    monkeypatch.setattr(
        init_crown_agent, "requests", types.SimpleNamespace(get=fake_get)
    )
    init_crown_agent._verify_servant_health({"alpha": "http://svc"})

    with TestClient(app) as client:
        resp = client.get("/metrics")
    assert 'servant_health_status{servant="alpha"} 1.0' in resp.text
