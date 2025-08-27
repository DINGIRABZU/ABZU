"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# Ensure the real SciPy package is loaded before tests potentially stub it.
try:  # pragma: no cover - optional dependency
    import scipy  # noqa: F401
except Exception:  # pragma: no cover - SciPy not installed
    pass

# Provide a minimal `huggingface_hub` stub for tests so that modules depending on
# it can be imported without pulling in the real library. The stub implements the
# small surface area used in the codebase and performs no network operations.
import spiral_os._hf_stub as hf_stub  # noqa: E402

sys.modules.setdefault("huggingface_hub", hf_stub)
sys.modules.setdefault("huggingface_hub.utils", hf_stub)

spec = importlib.util.spec_from_file_location(
    "seed", ROOT / "src" / "core" / "utils" / "seed.py"
)
seed_module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec and spec.loader
spec.loader.exec_module(seed_module)  # type: ignore[union-attr]
seed_all = seed_module.seed_all

import pytest  # noqa: E402

# Default to NumPy audio backend unless pydub and ffmpeg are fully available
if "AUDIO_BACKEND" not in os.environ:
    try:  # pragma: no cover - optional dependency

        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not found")
    except Exception:  # pragma: no cover - missing deps
        pass
    else:  # pragma: no cover - deps present
        os.environ["AUDIO_BACKEND"] = "pydub"


import emotion_registry  # noqa: E402
import emotional_state  # noqa: E402


@pytest.fixture()
def mock_emotion_state(tmp_path, monkeypatch):
    """Return a temporary emotion state file."""
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


@pytest.fixture(autouse=True)
def _seed_all():
    seed = int(os.getenv("PYTEST_SEED", "0"))
    seed_all(seed)


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
    str(ROOT / "tests" / "test_env_validation.py"),
    str(ROOT / "tests" / "test_crown_config.py"),
    str(ROOT / "tests" / "test_download_deepseek.py"),
    str(ROOT / "tests" / "test_dashboard_app.py"),
    str(ROOT / "tests" / "test_dashboard_usage.py"),
    str(ROOT / "tests" / "test_virtual_env_manager.py"),
    str(ROOT / "tests" / "test_sandbox_session.py"),
    str(ROOT / "tests" / "test_dependency_installer.py"),
    str(ROOT / "tests" / "test_bootstrap.py"),
    str(ROOT / "tests" / "test_avatar_lipsync.py"),
    str(ROOT / "tests" / "test_lip_sync.py"),
    str(ROOT / "tests" / "test_memory_search.py"),
    str(ROOT / "tests" / "test_memory_persistence.py"),
    str(ROOT / "tests" / "test_start_dev_agents_triage.py"),
    str(ROOT / "tests" / "test_gateway.py"),
    str(ROOT / "tests" / "test_core_scipy_smoke.py"),
    str(ROOT / "tests" / "test_download_models.py"),
    str(ROOT / "tests" / "test_download_model.py"),
    str(ROOT / "tests" / "test_api_endpoints.py"),
    str(ROOT / "tests" / "test_style_selection.py"),
    str(ROOT / "tests" / "test_prompt_engineering.py"),
    str(ROOT / "tests" / "test_model.py"),
    str(ROOT / "tests" / "test_logging_filters.py"),
    str(ROOT / "tests" / "test_rag_engine.py"),
    str(ROOT / "tests" / "test_data_pipeline.py"),
    str(ROOT / "tests" / "test_deployment_configs.py"),
    str(ROOT / "tests" / "test_memory_snapshot.py"),
    str(ROOT / "tests" / "performance" / "test_task_parser_performance.py"),
    str(ROOT / "tests" / "performance" / "test_vector_memory_performance.py"),
    str(ROOT / "tests" / "test_auto_retrain.py"),
    str(ROOT / "tests" / "test_autoretrain_full.py"),
    str(ROOT / "tests" / "test_learning_mutator.py"),
    str(ROOT / "tests" / "test_server.py"),
    str(ROOT / "tests" / "test_openwebui_state_updates.py"),
    str(ROOT / "tests" / "test_server_endpoints.py"),
    str(ROOT / "tests" / "test_insight_compiler.py"),
    str(ROOT / "tests" / "test_glm_command.py"),
    str(ROOT / "tests" / "test_media_audio.py"),
    str(ROOT / "tests" / "test_audio_backends.py"),
    str(ROOT / "tests" / "test_audio_segment.py"),
    str(ROOT / "tests" / "test_video_stream_helpers.py"),
    str(ROOT / "tests" / "test_media_video.py"),
    str(ROOT / "tests" / "test_media_avatar.py"),
    str(ROOT / "tests" / "test_introspection_api.py"),
    str(ROOT / "tests" / "test_lwm.py"),
    str(ROOT / "tests" / "test_emotional_state_logging.py"),
    str(ROOT / "tests" / "test_emotion_state.py"),
    str(ROOT / "tests" / "test_orchestrator.py"),
    str(ROOT / "tests" / "test_play_ritual_music_smoke.py"),
    str(ROOT / "tests" / "test_play_ritual_music.py"),
    str(ROOT / "tests" / "test_mix_tracks_emotion.py"),
    str(ROOT / "tests" / "test_sonic_emotion_mapper.py"),
    str(ROOT / "tests" / "test_transformation_smoke.py"),
    str(ROOT / "tests" / "test_hex_to_glyphs_smoke.py"),
    str(ROOT / "tests" / "test_interactions_jsonl.py"),
    str(ROOT / "tests" / "test_interactions_jsonl_integrity.py"),
    str(ROOT / "tests" / "test_corpus_memory_logging.py"),
    str(ROOT / "tests" / "test_logging_config_rotation.py"),
    str(ROOT / "tests" / "test_music_generation.py"),
    str(ROOT / "tests" / "test_music_generation_emotion.py"),
    str(ROOT / "tests" / "test_music_generation_streaming.py"),
    str(ROOT / "tests" / "test_music_backends_missing.py"),
    str(ROOT / "tests" / "test_albedo_state_machine.py"),
    str(ROOT / "tests" / "test_albedo_trust.py"),
    str(ROOT / "tests" / "test_vector_memory_extensions.py"),
    str(ROOT / "tests" / "test_cortex_memory.py"),
    str(ROOT / "tests" / "test_voice_cloner_cli.py"),
    str(ROOT / "tests" / "test_security_canary.py"),
    str(ROOT / "tests" / "agents" / "test_land_graph_geo_knowledge.py"),
    str(ROOT / "tests" / "agents" / "test_asian_gen.py"),
    str(ROOT / "tests" / "test_orchestration_master.py"),
    str(ROOT / "tests" / "memory" / "test_vector_memory.py"),
    str(ROOT / "tests" / "test_smoke_imports.py"),
    str(ROOT / "tests" / "agents" / "razar" / "test_ignition_builder.py"),
    str(ROOT / "tests" / "agents" / "razar" / "test_runtime_manager.py"),
    str(ROOT / "tests" / "agents" / "razar" / "test_boot_sequence.py"),
    str(ROOT / "tests" / "agents" / "razar" / "test_module_builder.py"),
    str(ROOT / "tests" / "agents" / "razar" / "test_planning_engine.py"),
    str(ROOT / "tests" / "agents" / "razar" / "test_pytest_runner.py"),
    str(ROOT / "tests" / "memory" / "test_sharded_memory_store.py"),
    str(ROOT / "tests" / "vision" / "test_yoloe_adapter.py"),
    str(ROOT / "tests" / "test_persona_profiles_loader.py"),
    str(ROOT / "tests" / "test_nazarick_messaging.py"),
    str(ROOT / "tests" / "agents" / "nazarick" / "test_ethics_manifesto.py"),
    str(ROOT / "tests" / "agents" / "nazarick" / "test_trust_matrix.py"),
}


def pytest_collection_modifyitems(config, items):
    """Skip tests that require heavy resources unless allowed."""
    skip_marker = pytest.mark.skip(reason="requires unavailable resources")
    for item in items:
        if str(item.fspath) not in ALLOWED_TESTS:
            item.add_marker(skip_marker)
