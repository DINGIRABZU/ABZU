from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

import tests.conftest as conftest_module

conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))


class FakeGLM:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def complete(self, prompt: str) -> str:
        self.calls.append(prompt)
        if prompt == identity_loader.HANDSHAKE_PROMPT:
            return identity_loader.HANDSHAKE_TOKEN
        return "LEGACY_SUMMARY"


@pytest.fixture(autouse=True)
def reload_identity_loader():
    global identity_loader
    import identity_loader as _identity_loader

    identity_loader = importlib.reload(_identity_loader)
    return identity_loader


def test_identity_loader_and_pyo3_stub_match(monkeypatch, tmp_path):
    ordered_chunks: list[dict[str, str]] = [
        {"text": "Mission brief", "source_path": "mission.md"},
        {"text": "Persona profile", "source_path": "persona.md"},
        {"text": "Doctrine fragment", "source_path": "doctrine.md"},
    ]

    source_map: dict[object, list[dict[str, str]]] = {
        identity_loader.MISSION_DOC: [ordered_chunks[0]],
        identity_loader.PERSONA_DOC: [ordered_chunks[1]],
        identity_loader.DOCTRINE_DOCS[0]: [ordered_chunks[2]],
    }

    def fake_load_source(path):  # pragma: no cover - helper
        return [dict(chunk) for chunk in source_map.get(path, [])]

    class DummyEmbedder:
        def embed_chunks(self, chunks):
            return [{**chunk, "embedding": [0.1]} for chunk in chunks]

    stored_vectors: list[list[dict[str, object]]] = []
    insight_updates: list[list[dict[str, object]]] = []

    monkeypatch.setattr(identity_loader, "_load_source", fake_load_source)
    monkeypatch.setattr(identity_loader, "embedder", DummyEmbedder())
    monkeypatch.setattr(identity_loader, "_store_vectors", stored_vectors.append)
    monkeypatch.setattr(identity_loader, "update_insights", insight_updates.append)
    identity_path = tmp_path / "identity.json"
    monkeypatch.setattr(identity_loader, "IDENTITY_FILE", identity_path)

    def build_prompt() -> str:
        sections = [
            (
                "Synthesize the mission, persona, and canonical "
                "doctrine into a cohesive identity summary."
            ),
            "Maintain covenantal tone and cite every pillar in the blended brief.",
        ]
        chunk_order: list[dict[str, str]] = []
        chunk_order.extend(source_map.get(identity_loader.MISSION_DOC, []))
        chunk_order.extend(source_map.get(identity_loader.PERSONA_DOC, []))
        for doc in identity_loader.DOCTRINE_DOCS:
            chunk_order.extend(source_map.get(doc, []))
        for chunk in chunk_order:
            sections.append(f"## Source: {chunk['source_path']}\n{chunk['text']}")
        return "\n\n".join(sections)

    expected_prompt = build_prompt()

    legacy_glm = FakeGLM()
    legacy_summary = identity_loader.load_identity(legacy_glm)
    assert legacy_summary == "LEGACY_SUMMARY"
    assert legacy_glm.calls == [expected_prompt, identity_loader.HANDSHAKE_PROMPT]

    if identity_loader.IDENTITY_FILE.exists():
        identity_loader.IDENTITY_FILE.unlink()

    neoabzu_stub = types.ModuleType("neoabzu_crown")

    def stub_load_identity(integration):
        prompt = build_prompt()
        summary = integration.complete(prompt)
        acknowledgement = integration.complete(identity_loader.HANDSHAKE_PROMPT)
        if acknowledgement.strip() != identity_loader.HANDSHAKE_TOKEN:
            raise RuntimeError(
                "identity loader handshake failed: expected CROWN-IDENTITY-ACK"
            )
        identity_loader.IDENTITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        identity_loader.IDENTITY_FILE.write_text(summary, encoding="utf-8")
        return summary

    neoabzu_stub.load_identity = stub_load_identity
    monkeypatch.setitem(sys.modules, "neoabzu_crown", neoabzu_stub)

    rust_glm = FakeGLM()
    rust_summary = neoabzu_stub.load_identity(rust_glm)

    assert rust_summary == legacy_summary
    assert rust_glm.calls == legacy_glm.calls
    assert identity_loader.IDENTITY_FILE.read_text(encoding="utf-8") == legacy_summary
    assert stored_vectors, "legacy path should store embedded chunks"
    assert insight_updates, "legacy path should emit insight updates"
