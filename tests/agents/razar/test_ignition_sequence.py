import json
import sys
import types
from pathlib import Path


from razar import boot_orchestrator as bo
from razar.crown_handshake import CrownResponse
from agents.nazarick.trust_matrix import TrustMatrix
from agents.operator_dispatcher import OperatorDispatcher


__version__ = "0.1.0"


def test_full_ignition_sequence(tmp_path: Path, monkeypatch):
    """Boot RAZAR and verify mission brief archiving and routing."""

    # isolate logs and state
    monkeypatch.setattr(bo, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(bo, "STATE_FILE", tmp_path / "state.json")

    # handshake stub triggers GLM4V launch
    class DummyHandshake:
        def __init__(self, url: str) -> None:  # pragma: no cover - simple
            self.url = url

        async def perform(self, brief_path: str) -> CrownResponse:
            assert Path(brief_path).exists()
            return CrownResponse("ack", [], {})

    monkeypatch.setattr(bo, "CrownHandshake", DummyHandshake)

    launched: list[list[str]] = []
    monkeypatch.setattr(bo.subprocess, "Popen", lambda cmd: launched.append(cmd))

    # run handshake and archive brief
    result = bo._perform_handshake([{"name": "glm"}])
    assert result.acknowledgement == "ack"
    assert launched, "GLM4V should launch when capability missing"

    brief_file = tmp_path / "mission_brief.json"
    assert brief_file.exists()
    archive_dir = tmp_path / "mission_briefs"
    archived = list(archive_dir.glob("mission_brief_*.json"))
    assert archived, "Archived mission brief not found"

    state = json.loads((tmp_path / "state.json").read_text())
    assert state["capabilities"] == []

    # load INANNA layers and invoke Albedo
    pkg = types.ModuleType("INANNA_AI")
    personality_layers = types.ModuleType("personality_layers")

    class AlbedoPersonality:
        def generate_response(self, text: str) -> str:
            return "persona"

    personality_layers.AlbedoPersonality = AlbedoPersonality
    pkg.personality_layers = personality_layers
    sys.modules["INANNA_AI"] = pkg
    sys.modules["INANNA_AI.personality_layers"] = personality_layers

    assert personality_layers.AlbedoPersonality().generate_response("hi") == "persona"

    # spawn Nazarick agent
    tm = TrustMatrix(tmp_path / "trust.db")
    assert tm.lookup_protocol("shalltear").startswith("nazarick_rank")
    tm.close()

    # operator command routing
    dispatcher = OperatorDispatcher(
        {"overlord": ["crown"]}, log_dir=tmp_path / "ops", worm_dir=tmp_path / "worm"
    )
    res = dispatcher.dispatch("overlord", "crown", lambda: {"ack": "ping"})
    assert res == {"ack": "ping"}
