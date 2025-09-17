# mypy: ignore-errors
"""Tests for the identity loading pipeline."""

from types import SimpleNamespace

import pytest

import identity_loader as il
import init_crown_agent as ic


class DummyGLM:
    def __init__(self, *, ack: str = "CROWN-IDENTITY-ACK"):
        self.prompts: list[str] = []
        self.ack = ack

    def complete(self, prompt: str, *, quantum_context: str | None = None) -> str:
        self.prompts.append(prompt)
        if "CROWN-IDENTITY-ACK" in prompt:
            return self.ack
        return "identity summary"


def test_identity_loader_persists(tmp_path, monkeypatch):
    mission = tmp_path / "docs" / "project_mission_vision.md"
    persona = tmp_path / "docs" / "persona_api_guide.md"
    mission.parent.mkdir(parents=True)
    mission.write_text("mission", encoding="utf-8")
    persona.write_text("persona", encoding="utf-8")

    monkeypatch.setattr(il, "MISSION_DOC", mission)
    monkeypatch.setattr(il, "PERSONA_DOC", persona)
    ident_file = tmp_path / "identity.json"
    monkeypatch.setattr(il, "IDENTITY_FILE", ident_file)

    genesis = tmp_path / "GENESIS" / "GENESIS_.md"
    spiral = tmp_path / "GENESIS" / "SPIRAL_LAWS_.md"
    vault = tmp_path / "CODEX" / "ACTIVATIONS" / "OATH_OF_THE_VAULT_.md"
    marrow = tmp_path / "INANNA_AI" / "MARROW CODE.md"
    song = tmp_path / "INANNA_AI" / "INANNA SONG.md"
    chapter = tmp_path / "INANNA_AI" / "Chapter I.md"
    for path, text in [
        (genesis, "genesis"),
        (spiral, "spiral"),
        (vault, "vault oath"),
        (marrow, "marrow"),
        (song, "song"),
        (chapter, "chapter"),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(
        il,
        "DOCTRINE_DOCS",
        (genesis, spiral, vault, marrow, song, chapter),
    )

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
    assert out1 == "identity summary"
    assert ident_file.read_text() == "identity summary"
    assert len(glm.prompts) == 2
    blended_prompt, ack_prompt = glm.prompts
    assert "mission" in blended_prompt
    assert "persona" in blended_prompt
    for marker in ("genesis", "spiral", "vault oath", "marrow", "song", "chapter"):
        assert marker in blended_prompt
    assert "CROWN-IDENTITY-ACK" in ack_prompt
    assert flags.get("add_vectors")
    assert "update" in flags

    out2 = il.load_identity(glm)
    assert out2 == "identity summary"
    assert len(glm.prompts) == 2


def test_identity_loader_requires_ack(tmp_path, monkeypatch):
    mission = tmp_path / "docs" / "project_mission_vision.md"
    persona = tmp_path / "docs" / "persona_api_guide.md"
    mission.parent.mkdir(parents=True)
    mission.write_text("mission", encoding="utf-8")
    persona.write_text("persona", encoding="utf-8")

    monkeypatch.setattr(il, "MISSION_DOC", mission)
    monkeypatch.setattr(il, "PERSONA_DOC", persona)
    ident_file = tmp_path / "identity.json"
    monkeypatch.setattr(il, "IDENTITY_FILE", ident_file)

    genesis = tmp_path / "GENESIS" / "GENESIS_.md"
    genesis.parent.mkdir(parents=True, exist_ok=True)
    genesis.write_text("genesis", encoding="utf-8")
    monkeypatch.setattr(il, "DOCTRINE_DOCS", (genesis,))

    glm = DummyGLM(ack="nope")

    with pytest.raises(RuntimeError, match="CROWN-IDENTITY-ACK"):
        il.load_identity(glm)

    assert not ident_file.exists()
    assert len(glm.prompts) == 2


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
