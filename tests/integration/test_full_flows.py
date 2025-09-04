from __future__ import annotations

import importlib
import json
import logging
import sys
import types
from pathlib import Path


import tests.conftest as conftest_module

conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class DummyModel:
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[1.0, 0.0] if "hello" in t else [0.0, 1.0] for t in texts]


class RagDummyCollection:
    def __init__(self):
        self.records = []

    def add(self, ids, embeddings, metadatas):
        for emb, meta in zip(embeddings, metadatas):
            self.records.append((emb, meta))

    def query(self, query_embeddings, n_results, **_):
        q = query_embeddings[0]
        sims = [float(sum(a * b for a, b in zip(e, q))) for e, _ in self.records]
        order = list(reversed(sorted(range(len(sims)), key=lambda i: sims[i])))[
            :n_results
        ]
        return {
            "embeddings": [[self.records[i][0] for i in order]],
            "metadatas": [[self.records[i][1] for i in order]],
        }


def test_boot_sequence_flow(tmp_path, monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        from dataclasses import dataclass

        @dataclass
        class CrownResponse:
            acknowledgement: str = ""
            capabilities: list[str] | None = None
            downtime: dict | None = None

        async def _perform(path: str) -> CrownResponse:
            return CrownResponse(capabilities=["GLM4V"])  # avoid model launch

        stubs = {
            "razar.crown_handshake": types.SimpleNamespace(
                perform=_perform, CrownResponse=CrownResponse
            ),
            "razar.ai_invoker": types.SimpleNamespace(handover=lambda name, msg: False),
            "razar.doc_sync": types.SimpleNamespace(sync_docs=lambda: None),
            "razar.mission_logger": types.SimpleNamespace(
                log_event=lambda *a, **k: None
            ),
            "razar.health_checks": types.SimpleNamespace(
                run=lambda name: True, CHECKS={}
            ),
            "razar.quarantine_manager": types.SimpleNamespace(
                is_quarantined=lambda name: False,
                quarantine_component=lambda comp, reason: None,
            ),
            "agents.nazarick.service_launcher": types.SimpleNamespace(
                launch_required_agents=lambda: None
            ),
        }
        for name, mod in stubs.items():
            sys.modules[name] = mod

        boot_orchestrator = importlib.import_module("razar.boot_orchestrator")
        monkeypatch.setattr(boot_orchestrator, "LOGS_DIR", tmp_path)
        monkeypatch.setattr(boot_orchestrator, "STATE_FILE", tmp_path / "state.json")
        monkeypatch.setattr(
            boot_orchestrator, "HISTORY_FILE", tmp_path / "history.json"
        )
        config = tmp_path / "boot.json"
        comp = {
            "name": "svc",
            "command": ["python", "-c", "import time; time.sleep(0.1)"],
            "health_check": ["python", "-c", "import sys; sys.exit(0)"],
        }
        config.write_text(json.dumps({"components": [comp]}))
        monkeypatch.setattr(
            sys,
            "argv",
            ["boot_orchestrator", "--config", str(config), "--retries", "0"],
        )
        boot_orchestrator.main()
    assert caplog.text == ""


def test_memory_snapshot_cycle(tmp_path, monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        import emotional_state

        monkeypatch.setitem(sys.modules, "memory", types.SimpleNamespace())
        monkeypatch.setitem(
            sys.modules,
            "memory.narrative_engine",
            types.SimpleNamespace(StoryEvent=dict),
        )
        import vector_memory

        monkeypatch.setattr(emotional_state, "_save_state", lambda: None)
        monkeypatch.setattr(emotional_state, "_save_registry", lambda: None)
        monkeypatch.setattr(vector_memory, "_log_narrative", lambda *a, **k: None)

        monkeypatch.setattr(emotional_state, "STATE_FILE", tmp_path / "state.json")
        monkeypatch.setattr(emotional_state, "REGISTRY_FILE", tmp_path / "reg.json")
        monkeypatch.setattr(emotional_state, "EVENT_LOG", tmp_path / "events.jsonl")
        emotional_state._STATE.clear()
        emotional_state._REGISTRY.clear()
        emotional_state.set_last_emotion("joy")
        snap = tmp_path / "emotion.json"
        emotional_state.snapshot(snap)
        emotional_state.set_last_emotion("sad")
        emotional_state.restore(snap)
        assert emotional_state.get_last_emotion() == "joy"

        class VMCollection:
            def __init__(self):
                self.data = {"ids": [], "embeddings": [], "metadatas": []}

            def add(self, ids, embeddings, metadatas):
                if isinstance(ids, list):
                    self.data["ids"].extend(ids)
                    self.data["embeddings"].extend(embeddings)
                    self.data["metadatas"].extend(metadatas)
                else:
                    self.data["ids"].append(ids)
                    self.data["embeddings"].append(embeddings)
                    self.data["metadatas"].append(metadatas)

            def get(self, ids=None):
                if ids is None:
                    return self.data
                res = {"ids": [], "embeddings": [], "metadatas": []}
                for i in ids:
                    idx = self.data["ids"].index(i)
                    for key in res:
                        res[key].append(self.data[key][idx])
                return res

            def delete(self, ids):
                for i in ids:
                    idx = self.data["ids"].index(i)
                    for key in self.data:
                        self.data[key].pop(idx)

        col = VMCollection()
        monkeypatch.setattr(vector_memory, "_COLLECTION", col)
        monkeypatch.setattr(vector_memory, "_get_collection", lambda: col)
        monkeypatch.setattr(vector_memory, "_EMBED", lambda s: [1.0, 0.0])
        monkeypatch.setattr(vector_memory, "_DIR", tmp_path)
        monkeypatch.setattr(vector_memory, "NARRATIVE_LOG", tmp_path / "narrative.log")
        vector_memory.add_vector("hello", {})
        snap_vm = tmp_path / "vm.json"
        vector_memory.snapshot(snap_vm)
        col.data = {"ids": [], "embeddings": [], "metadatas": []}
        vector_memory.restore(snap_vm)
        assert col.data["metadatas"][0]["text"] == "hello"
    assert caplog.text == ""


def test_rag_route(tmp_path, monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        import crown_query_router
        from rag import (
            embedder as rag_embedder,
            parser as rag_parser,
            retriever as rag_retriever,
        )

        dummy_np = types.ModuleType("numpy")

        class NPArray(list):
            def tolist(self):
                return list(self)

            def __matmul__(self, other):
                return sum(a * b for a, b in zip(self, other))

            def flatten(self):
                return self

        def _arr(x, dtype=None):
            return NPArray(x)

        dummy_np.array = _arr
        dummy_np.asarray = _arr
        dummy_np.linalg = types.SimpleNamespace(
            norm=lambda v: sum(i * i for i in v) ** 0.5
        )
        dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
        sys.modules.setdefault("numpy", dummy_np)
        sys.modules.setdefault("librosa", types.ModuleType("librosa"))
        sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

        base = tmp_path / "inputs"
        base.mkdir()
        f = base / "doc.txt"
        f.write_text("hello world", encoding="utf-8")
        chunks = rag_parser.load_inputs(base)
        monkeypatch.setattr(
            rag_embedder, "SentenceTransformer", lambda name: DummyModel()
        )
        rag_embedder._MODEL = None
        embedded = rag_embedder.embed_chunks(chunks)
        col = RagDummyCollection()
        monkeypatch.setattr(rag_retriever, "get_collection", lambda name: col)
        monkeypatch.setattr(
            rag_retriever.rag_embedder, "_get_model", lambda: DummyModel()
        )
        col.add(
            ["1"],
            [embedded[0]["embedding"]],
            [{k: v for k, v in embedded[0].items() if k != "embedding"}],
        )
        res = crown_query_router.route_query("hello", "Sage")
        assert (
            res and res[0]["text"] == "hello world" and res[0]["source_path"] == str(f)
        )
    assert caplog.text == ""


def test_nlq_training(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        trainings = []
        monkeypatch.setitem(
            sys.modules,
            "vanna",
            types.SimpleNamespace(
                __stub__=False, train=lambda ddl: trainings.append(ddl)
            ),
        )
        import nlq_api

        failed = nlq_api._train_vanna()
        assert failed == []
        assert trainings
    assert caplog.text == ""
