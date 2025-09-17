# mypy: ignore-errors
"""Tests for the identity loading pipeline."""

from pathlib import Path
from types import SimpleNamespace

import identity_loader as il
import init_crown_agent as ic


class DummyGLM:
    def __init__(self):
        self.calls = 0
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, quantum_context: str | None = None) -> str:
        self.calls += 1
        self.prompts.append(prompt)
        return prompt


def test_identity_loader_persists(tmp_path, monkeypatch):
    mission = tmp_path / "docs" / "project_mission_vision.md"
    persona = tmp_path / "docs" / "persona_api_guide.md"
    protocol = tmp_path / "docs" / "The_Absolute_Protocol.md"
    blueprint = tmp_path / "docs" / "system_blueprint.md"
    awakening = tmp_path / "docs" / "awakening_overview.md"
    mission.parent.mkdir(parents=True)
    mission.write_text("mission", encoding="utf-8")
    persona.write_text("persona", encoding="utf-8")
    protocol.write_text("protocol doctrine", encoding="utf-8")
    blueprint.write_text("blueprint doctrine", encoding="utf-8")
    awakening.write_text("awakening doctrine", encoding="utf-8")

    monkeypatch.setattr(il, "MISSION_DOC", mission)
    monkeypatch.setattr(il, "PERSONA_DOC", persona)
    ident_file = tmp_path / "identity.json"
    monkeypatch.setattr(il, "IDENTITY_FILE", ident_file)

    seen: set[Path] = set()

    def fake_load_inputs(directory):
        if directory in seen:
            return []
        seen.add(directory)
        return [
            {"text": mission.read_text(), "source_path": str(mission)},
            {"text": persona.read_text(), "source_path": str(persona)},
            {"text": protocol.read_text(), "source_path": str(protocol)},
            {"text": blueprint.read_text(), "source_path": str(blueprint)},
            {"text": awakening.read_text(), "source_path": str(awakening)},
        ]

    monkeypatch.setattr(il.parser, "load_inputs", fake_load_inputs)

    def fake_embed_chunks(chunks):
        return [
            {"text": c["text"], "source_path": c["source_path"], "embedding": [1.0]}
            for c in chunks
        ]

    monkeypatch.setattr(il.embedder, "embed_chunks", fake_embed_chunks)

    flags = {}

    def fake_add_vectors(texts, metas):
        flags["add_vectors"] = True

    monkeypatch.setattr(il.vector_memory, "add_vectors", fake_add_vectors)

    def fake_update(entries):
        flags["update"] = entries

    monkeypatch.setattr(il, "update_insights", fake_update)

    glm = DummyGLM()
    out1 = il.load_identity(glm)
    assert "mission" in out1
    assert "persona" in out1
    assert "protocol doctrine" in out1
    assert "blueprint doctrine" in out1
    assert "awakening doctrine" in out1
    assert ident_file.read_text() == out1
    assert glm.calls == 1
    assert flags.get("add_vectors")
    assert "update" in flags

    out2 = il.load_identity(glm)
    assert out2 == out1
    assert glm.calls == 1


def test_initialize_triggers_identity(monkeypatch):
    dummy_glm = DummyGLM()

    monkeypatch.setattr(ic, "GLMIntegration", lambda *a, **k: dummy_glm)
    monkeypatch.setattr(ic, "_init_memory", lambda cfg: None)
    monkeypatch.setattr(ic, "_init_servants", lambda cfg: None)
    monkeypatch.setattr(ic, "_verify_servant_health", lambda servants: None)
    monkeypatch.setattr(ic, "_check_glm", lambda integration: None)

    called = SimpleNamespace(flag=False)

    def fake_load(integration):
        called.flag = True

    monkeypatch.setattr(ic, "load_identity", fake_load)

    ic.initialize_crown()
    assert called.flag


def test_initialize_stores_identity_summary(monkeypatch):
    dummy_glm = DummyGLM()
    vector_calls: dict[str, dict] = {}
    corpus_calls: dict[str, dict] = {}

    class DummyVector:
        def add_vector(self, text, metadata):
            vector_calls["text"] = text
            vector_calls["metadata"] = metadata

    def fake_add_entry(text, tone, *, metadata=None):
        corpus_calls["text"] = text
        corpus_calls["metadata"] = metadata or {}

    monkeypatch.setattr(ic, "GLMIntegration", lambda *a, **k: dummy_glm)
    monkeypatch.setattr(ic, "_init_memory", lambda cfg: None)
    monkeypatch.setattr(ic, "_init_servants", lambda cfg: None)
    monkeypatch.setattr(ic, "_verify_servant_health", lambda servants: None)
    monkeypatch.setattr(ic, "_check_glm", lambda integration: None)
    monkeypatch.setattr(ic, "vector_memory", DummyVector())
    monkeypatch.setattr(
        ic,
        "corpus_memory",
        SimpleNamespace(add_entry=fake_add_entry, vector_memory=None),
    )
    monkeypatch.setattr(ic, "load_identity", lambda integration: "identity summary")

    ic.initialize_crown()

    assert vector_calls["text"] == "identity summary"
    assert vector_calls["metadata"]["type"] == "identity_summary"
    assert corpus_calls["text"] == "identity summary"
    assert corpus_calls["metadata"]["type"] == "identity_summary"
    assert corpus_calls["metadata"]["stage"] == "crown_boot"
