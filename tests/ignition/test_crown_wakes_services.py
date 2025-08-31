import sys
import types
from pathlib import Path

import numpy as np
import pytest

from razar.crown_handshake import CrownResponse

__version__ = "0.1.0"


def test_crown_wakes_services(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Handshake triggers Nazarick and Bana startup with logs."""

    # Avoid heavy modules during import
    monkeypatch.setitem(sys.modules, "razar.doc_sync", types.ModuleType("doc_sync"))
    monkeypatch.setitem(
        sys.modules, "razar.health_checks", types.ModuleType("health_checks")
    )
    monkeypatch.setitem(sys.modules, "agents.guardian", types.ModuleType("guardian"))
    monkeypatch.setitem(sys.modules, "agents.cocytus", types.ModuleType("cocytus"))

    from razar import boot_orchestrator as bo
    from agents.nazarick import service_launcher as sl
    from agents.bana import bio_adaptive_narrator as ban

    monkeypatch.setattr(bo, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(bo, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setenv("CROWN_WS_URL", "ws://example")

    class DummyHandshake:
        def __init__(self, url: str) -> None:  # pragma: no cover - trivial
            self.url = url

        async def perform(self, brief_path: str) -> CrownResponse:
            assert Path(brief_path).exists()
            return CrownResponse("ok", ["GLM4V"], {})

    monkeypatch.setattr(bo, "CrownHandshake", DummyHandshake)

    launches: list[list[str]] = []
    monkeypatch.setattr(sl, "REQUIRED_AGENTS", {"nazarick": ["echo", "nazarick"]})
    monkeypatch.setattr(sl.subprocess, "Popen", lambda cmd: launches.append(cmd))

    resp = bo._perform_handshake([{"name": "nazarick"}])
    assert resp.acknowledgement == "ok"
    assert list((tmp_path / "mission_briefs").glob("*.json")), "mission brief archived"

    events = sl.launch_required_agents()
    assert events[0]["status"] == "launched"
    assert launches == [["echo", "nazarick"]]

    def fake_ecg(signal, sampling_rate, show):
        return {"heart_rate": np.array([72.0])}

    monkeypatch.setattr(ban, "ecg", types.SimpleNamespace(ecg=fake_ecg))

    class DummyGenerator:
        def __call__(self, prompt, max_new_tokens, num_return_sequences):  # noqa: D401
            return [{"generated_text": "Saga"}]

    monkeypatch.setattr(ban, "pipeline", lambda *a, **k: DummyGenerator())

    bana_dir = tmp_path / "bana"

    def log_story(text: str) -> None:
        bana_dir.mkdir(parents=True, exist_ok=True)
        (bana_dir / "story.md").write_text(text)

    monkeypatch.setattr("memory.narrative_engine.log_story", log_story)

    story = ban.generate_story(np.ones(1000))
    assert story == "Saga"
    assert (bana_dir / "story.md").read_text() == "Saga"
