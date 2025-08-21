import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.personality_layers.albedo import (
    AlbedoPersonality,
    AlchemicalPersona,
    GLMIntegration,
    State,
    glm_integration,
    state_contexts,
)


class DummyResponse:
    def __init__(self, text: str) -> None:
        self._text = text
        self.text = text

    def json(self):
        return {"text": self._text}

    def raise_for_status(self):
        return None


def _patch_requests(monkeypatch, prompts, replies):
    dummy = types.ModuleType("requests")

    dummy.RequestException = Exception

    def post(url, json, timeout=10, headers=None):
        prompts.append((json.get("prompt"), json.get("quantum_context")))
        return DummyResponse(replies.pop(0))

    dummy.post = post
    monkeypatch.setattr(glm_integration, "requests", dummy)


def test_entity_recognition_and_state_transitions():
    core = AlchemicalPersona()
    assert [s.value for s in State] == [
        "nigredo",
        "albedo",
        "rubedo",
        "citrinitas",
    ]

    assert core.state is State.NIGREDO
    core.advance()
    assert core.state is State.ALBEDO
    core.advance()
    assert core.state is State.RUBEDO
    core.advance()
    assert core.state is State.CITRINITAS
    core.advance()
    assert core.state is State.NIGREDO


def test_prompt_formatting_and_glm(monkeypatch):
    prompts = []
    replies = ["one", "two", "three"]
    _patch_requests(monkeypatch, prompts, replies)

    monkeypatch.setattr(
        state_contexts,
        "CONTEXTS",
        {
            "nigredo": "N-{entity}-{triggers}-{text}-{qcontext}",
            "albedo": "A-{entity}-{triggers}-{text}-{qcontext}",
            "rubedo": "R-{entity}-{triggers}-{text}-{qcontext}",
        },
    )

    layer = AlbedoPersonality()
    text = "I love Alice"
    out1 = layer.generate_response(text, quantum_context="Q1")
    out2 = layer.generate_response(text, quantum_context="Q2")
    out3 = layer.generate_response(text, quantum_context="Q3")

    assert [out1, out2, out3] == ["one", "two", "three"]
    expected = [
        ("N-person-affection-" + text + "-Q1", "Q1"),
        ("A-person-affection-" + text + "-Q2", "Q2"),
        ("R-person-affection-" + text + "-Q3", "Q3"),
    ]
    assert prompts == expected
    assert layer.state == "nigredo"


def test_env_overrides_endpoint(monkeypatch):
    monkeypatch.setenv("GLM_API_URL", "http://foo")
    gi = GLMIntegration()
    assert gi.endpoint == "http://foo"
