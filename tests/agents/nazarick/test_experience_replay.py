from __future__ import annotations

from agents import experience_replay


def test_store_and_replay_similarity_order(monkeypatch):
    stored = []

    class DummyVM:
        def add_vector(self, text, meta):  # pragma: no cover - simple
            stored.append({"text": text, **meta})

        def search(self, query, filter=None, k=5, scoring="similarity"):
            def score(t: str) -> int:
                return len(set(query.split()) & set(t.split()))

            results = []
            for item in stored:
                if filter and item.get("agent_id") != filter.get("agent_id"):
                    continue
                results.append({"text": item["text"], "score": score(item["text"])})
            results.sort(key=lambda r: r["score"], reverse=True)
            return results[:k]

    dummy = DummyVM()
    monkeypatch.setattr(experience_replay, "vector_memory", dummy)

    logs = []
    monkeypatch.setattr(experience_replay, "log_agent_interaction", logs.append)

    experience_replay.store_event("a", "hello world")
    experience_replay.store_event("a", "hello there")
    experience_replay.store_event("a", "goodbye moon")

    hits = experience_replay.replay("a", "hello world")

    assert hits[:2] == ["hello world", "hello there"]
    assert len(logs) == 3
