"""Regression tests verifying deterministic Crown replay captures."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import types
from pathlib import Path

import pytest

# Stub heavy optional dependencies before importing orchestrator modules
for module_name in [
    "opensmile",
    "librosa",
    "cv2",
    "pydub",
    "pydub.playback",
    "simpleaudio",
    "soundfile",
]:
    sys.modules.setdefault(module_name, types.ModuleType(module_name))

from scripts import crown_capture_replays as ccr


def _load_baseline(path: Path) -> dict[str, object]:
    if not path.exists():
        raise AssertionError(f"Missing replay baseline for {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _record_summary(path: str | None, payload: dict[str, object]) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_crown_replay_determinism(crown_replay_env: dict[str, Path]) -> None:
    """Replaying recorded Crown scenarios must remain drift-free."""

    scenarios = ccr._load_scenarios(Path("crown/replay_scenarios.yaml"))
    baseline_dir = Path("logs/crown_replays")

    divergences: list[str] = []
    start = time.perf_counter()

    for scenario in scenarios:
        scenario_id = str(scenario["id"])
        capture = asyncio.run(ccr._run_scenario(scenario))

        baseline_payload = _load_baseline(baseline_dir / f"{scenario_id}.json")
        baseline = baseline_payload["baseline"]

        comparisons = {
            "model": (baseline["model"], capture.model),
            "emotion": (baseline["emotion"], capture.emotion),
            "state": (baseline["state"], capture.state),
            "result_hash": (baseline["result_hash"], capture.result_hash),
            "audio_hash": (baseline["audio_hash"], capture.audio_hash),
            "video_hash": (baseline["video_hash"], capture.video_hash),
            "servant_prompt": (baseline.get("servant_prompt"), capture.servant_prompt),
        }

        for field, (expected, observed) in comparisons.items():
            if expected != observed:
                divergences.append(
                    (
                        f"{scenario_id}.{field}: expected {expected!r}, "
                        f"observed {observed!r}"
                    )
                )

    duration = time.perf_counter() - start
    summary_payload = {
        "scenarios": len(scenarios),
        "divergences": len(divergences),
        "duration_seconds": duration,
        "details": divergences,
    }
    _record_summary(os.environ.get("CROWN_REPLAY_SUMMARY_PATH"), summary_payload)

    if divergences:
        formatted = "\n".join(divergences)
        pytest.fail(f"Crown replay divergences detected:\n{formatted}")
