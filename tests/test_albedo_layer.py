import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.personality_layers.albedo import (
    AlbedoPersonality,
    GLMIntegration,
    state_contexts,
    glm_integration,
)


class DummyResponse:
    def __init__(self, text: str):
        self._text = text
        self.text = text

    def json(self):
        return {"text": self._text}

    def raise_for_status(self):
        return None


def _patch_requests(monkeypatch, prompts):
    dummy = types.ModuleType("requests")

    dummy.RequestException = Exception

    def post(url, json, timeout=10, headers=None):
        prompts.append((json.get("prompt"), json.get("quantum_context"), headers))
        return DummyResponse("reply")

    dummy.post = post
    monkeypatch.setattr(glm_integration, "requests", dummy)


def _patch_requests_capture(monkeypatch, log):
    dummy = types.ModuleType("requests")
    dummy.RequestException = Exception

    def post(url, json, timeout=10, headers=None):
        log.append((url, json.get("prompt"), json.get("quantum_context"), headers))
        return DummyResponse("reply")

    dummy.post = post
    monkeypatch.setattr(glm_integration, "requests", dummy)


def test_state_transitions(monkeypatch):
    prompts = []
    _patch_requests(monkeypatch, prompts)
    layer = AlbedoPersonality()

    assert layer.state == "nigredo"
    layer.generate_response("hi")
    assert layer.state == "albedo"
    layer.generate_response("hi")
    assert layer.state == "rubedo"
    layer.generate_response("hi")
    assert layer.state == "citrinitas"
    layer.generate_response("hi")
    assert layer.state == "nigredo"


def test_prompt_construction(monkeypatch):
    prompts = []
    _patch_requests(monkeypatch, prompts)
    monkeypatch.setattr(state_contexts, "CONTEXTS", {"nigredo": "A {text} {qcontext}"})
    layer = AlbedoPersonality()
    layer.generate_response("hello", quantum_context="qc")
    assert prompts == [("A hello qc", "qc", None)]


def test_env_overrides_endpoint(monkeypatch):
    monkeypatch.setenv("GLM_API_URL", "http://foo")
    gi = GLMIntegration()
    assert gi.endpoint == "http://foo"


def test_glm_header(monkeypatch):
    prompts = []
    monkeypatch.setenv("GLM_API_KEY", "tok")
    _patch_requests(monkeypatch, prompts)
    GLMIntegration().complete("hello")
    assert prompts == [("hello", None, {"Authorization": "Bearer tok"})]


def test_state_cycle_wraparound(monkeypatch):
    prompts = []
    _patch_requests(monkeypatch, prompts)
    layer = AlbedoPersonality()

    states = []
    for _ in range(4):
        layer.generate_response("hi")
        states.append(layer.state)

    assert states == ["albedo", "rubedo", "citrinitas", "nigredo"]


def test_env_vars_honored(monkeypatch):
    calls = []
    monkeypatch.setenv("GLM_API_URL", "http://bar")
    monkeypatch.setenv("GLM_API_KEY", "key")
    _patch_requests_capture(monkeypatch, calls)
    GLMIntegration().complete("yo")
    assert calls == [("http://bar", "yo", None, {"Authorization": "Bearer key"})]


def test_glm_error_safe_message(monkeypatch):
    class DummyExc(Exception):
        pass

    dummy = types.ModuleType("requests")
    dummy.RequestException = DummyExc

    def post(url, json, timeout=10, headers=None):
        raise DummyExc("fail")

    dummy.post = post
    monkeypatch.setattr(glm_integration, "requests", dummy)
    out = GLMIntegration().complete("hi")
    assert out == glm_integration.SAFE_ERROR_MESSAGE


def test_glm_missing_requests(monkeypatch):
    monkeypatch.setattr(glm_integration, "requests", None)
    out = GLMIntegration().complete("hi")
    assert out == glm_integration.SAFE_ERROR_MESSAGE
