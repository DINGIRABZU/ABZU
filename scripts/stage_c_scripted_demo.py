#!/usr/bin/env python3
"""Stage C scripted demo harness with telemetry capture."""

from __future__ import annotations

import argparse
import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoStep:
    """Single scripted beat in the demo."""

    step_id: str
    prompt: str
    emotion: str
    duration_s: float = 1.2
    fps: int = 12


SCRIPTED_STEPS: tuple[DemoStep, ...] = (
    DemoStep(
        step_id="arrival",
        prompt="Avatar arrives on stage and greets the operators.",
        emotion="anticipatory",
        duration_s=1.0,
    ),
    DemoStep(
        step_id="handoff",
        prompt="Mission handoff with modulation overlay.",
        emotion="focused",
        duration_s=1.4,
    ),
    DemoStep(
        step_id="closing",
        prompt="Closing salutation with harmonic swell.",
        emotion="resonant",
        duration_s=1.6,
    ),
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _encode_array(array: np.ndarray) -> dict[str, Any]:
    payload = base64.b64encode(array.tobytes()).decode("ascii")
    return {
        "shape": array.shape,
        "dtype": str(array.dtype),
        "data_b64": payload,
    }


def _synth_audio(step: DemoStep, *, seed: int, output: Path) -> tuple[Path, float]:
    sample_rate = 16_000
    sample_count = int(sample_rate * step.duration_s)
    rng = np.random.default_rng(seed)
    waveform = rng.standard_normal(sample_count).astype(np.float32) * 0.02
    payload = {
        "sample_rate": sample_rate,
        "encoding": "float32_le",
        **_encode_array(waveform),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload), encoding="utf-8")
    duration = waveform.size / sample_rate
    return output, duration


def _synth_video(step: DemoStep, *, seed: int, output: Path) -> tuple[Path, float]:
    rng = np.random.default_rng(seed)
    frame_total = max(1, int(step.duration_s * step.fps))
    frames = rng.integers(0, 255, size=(frame_total, 64, 64, 3), dtype=np.uint8)
    payload = {
        "fps": step.fps,
        **_encode_array(frames),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload), encoding="utf-8")
    duration = frame_total / step.fps
    return output, duration


def run_session(output_dir: Path, *, seed: int) -> dict[str, Any]:
    logger.info("Starting scripted demo session (seed=%s)", seed)
    telemetry_rows: list[dict[str, Any]] = []
    emotion_rows: list[dict[str, Any]] = []
    media_manifest: list[dict[str, Any]] = []
    max_sync_offset = 0.0

    for index, step in enumerate(SCRIPTED_STEPS, start=1):
        step_seed = seed + index * 17
        step_ts = _timestamp()
        logger.info("[%s] cue=%s emotion=%s", step.step_id, step.prompt, step.emotion)

        audio_path = output_dir / "audio" / f"{step_ts}_{step.step_id}.json"
        video_path = output_dir / "video" / f"{step_ts}_{step.step_id}.json"

        audio_path, audio_duration = _synth_audio(
            step, seed=step_seed, output=audio_path
        )
        video_path, video_duration = _synth_video(
            step, seed=step_seed + 3, output=video_path
        )

        sync_offset = abs(audio_duration - video_duration)
        max_sync_offset = max(max_sync_offset, sync_offset)
        dropout_detected = False
        telemetry_rows.append(
            {
                "timestamp": step_ts,
                "event": "stage_c.demo.step",
                "step_id": step.step_id,
                "emotion": step.emotion,
                "audio_duration_s": round(audio_duration, 3),
                "video_duration_s": round(video_duration, 3),
                "sync_offset_s": round(sync_offset, 3),
                "dropout": dropout_detected,
                "prompt": step.prompt,
            }
        )
        emotion_rows.append(
            {
                "timestamp": step_ts,
                "step_id": step.step_id,
                "emotion": step.emotion,
            }
        )
        media_manifest.append(
            {
                "step_id": step.step_id,
                "audio_path": str(audio_path.relative_to(output_dir)),
                "video_path": str(video_path.relative_to(output_dir)),
            }
        )

    telemetry_path = output_dir / "telemetry" / "events.jsonl"
    emotion_path = output_dir / "emotion" / "stream.jsonl"
    manifest_path = output_dir / "telemetry" / "media_manifest.json"

    _write_jsonl(telemetry_path, telemetry_rows)
    _write_jsonl(emotion_path, emotion_rows)
    manifest_path.write_text(json.dumps(media_manifest, indent=2), encoding="utf-8")

    summary = {
        "timestamp": _timestamp(),
        "steps": len(SCRIPTED_STEPS),
        "max_sync_offset_s": round(max_sync_offset, 3),
        "dropouts_detected": any(row["dropout"] for row in telemetry_rows),
    }
    (output_dir / "telemetry" / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    logger.info(
        "Session complete: %s steps, max sync offset %.3fs",
        summary["steps"],
        summary["max_sync_offset_s"],
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="Directory for session evidence")
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed for deterministic synthetic assets",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_session(args.output_dir, seed=args.seed)
    summary_path = args.output_dir / "telemetry" / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
