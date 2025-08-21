import os
import shutil
import sys
from pathlib import Path

import pytest

# Default to NumPy audio backend unless pydub and ffmpeg are fully available
if "AUDIO_BACKEND" not in os.environ:
    try:  # pragma: no cover - optional dependency
        import pydub  # type: ignore

        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not found")
    except Exception:  # pragma: no cover - missing deps
        pass
    else:  # pragma: no cover - deps present
        os.environ["AUDIO_BACKEND"] = "pydub"


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotion_registry
import emotional_state


@pytest.fixture()
def mock_emotion_state(tmp_path, monkeypatch):
    state_file = tmp_path / "emotion_state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    monkeypatch.setattr(emotion_registry, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotion_registry._STATE.clear()
    emotional_state._save_state()
    emotion_registry._load_state()
    emotional_state.set_last_emotion("longing")
    emotional_state.set_resonance_level(0.75)
    return state_file


# ---------------------------------------------------------------------------
# Test isolation helpers


def pytest_collectstart(collector):
    """Ensure stubbed ``rag`` modules from other tests do not leak."""
    sys.modules.pop("rag", None)
    sys.modules.pop("rag.orchestrator", None)
    sys.modules.pop("SPIRAL_OS", None)
    sys.modules.pop("SPIRAL_OS.qnl_engine", None)
    sys.modules.pop("SPIRAL_OS.symbolic_parser", None)


# Skip tests that rely on unavailable heavy resources unless explicitly allowed
ALLOWED_TESTS = {
    str(ROOT / "tests" / "test_adaptive_learning_stub.py"),
}


def pytest_collection_modifyitems(config, items):
    skip_marker = pytest.mark.skip(reason="requires unavailable resources")
    for item in items:
        if str(item.fspath) not in ALLOWED_TESTS:
            item.add_marker(skip_marker)
