#!/usr/bin/env python3
"""Stage C demo runner capturing audio, avatar renders, and telemetry."""

from __future__ import annotations

import argparse
import base64
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
for candidate in (REPO_ROOT, REPO_ROOT / "src"):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import emotional_state
import numpy as np
from INANNA_AI import tts_coqui
from src.audio.telemetry import telemetry
from src.core import avatar_expression_engine

try:  # pragma: no cover - optional dependency
    import imageio.v2 as imageio
except Exception as exc:  # pragma: no cover - dependency required at runtime
    raise RuntimeError("imageio is required to render avatar GIFs") from exc

EVENT_LOG = Path("data/emotion_events.jsonl")


class _TelemetryLogHandler(logging.Handler):
    """Parse telemetry log lines into structured events."""

    def __init__(self, sink: list[dict]) -> None:
        super().__init__(level=logging.INFO)
        self._sink = sink

    def emit(
        self, record: logging.LogRecord
    ) -> None:  # pragma: no cover - logging glue
        message = record.getMessage()
        if "telemetry=" not in message:
            return
        payload = message.split("telemetry=", 1)[1]
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return
        self._sink.append(data)


@dataclass
class Scenario:
    """Configuration for a scripted demo session."""

    session_id: str
    text: str
    emotion: str
    layer: str | None = None


@dataclass
class SessionResult:
    """Collected evidence for a single run."""

    session: Scenario
    start_utc: str
    end_utc: str
    audio_path: Path
    avatar_path: Path
    telemetry_path: Path
    emotion_log_path: Path
    dropouts: List[dict]


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _read_emotion_log() -> List[str]:
    if EVENT_LOG.exists():
        return EVENT_LOG.read_text(encoding="utf-8").splitlines()
    return []


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_base64(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    target.write_text(encoded, encoding="utf-8")


def _extract_new_events(before: Iterable[str], after: Iterable[str]) -> List[str]:
    before_list = list(before)
    return list(after)[len(before_list) :]


def run_session(root: Path, scenario: Scenario) -> SessionResult:
    """Execute a single demo session and capture evidence."""

    session_dir = root / scenario.session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    logging.info(
        "=== %s :: starting demo (emotion=%s, layer=%s)",
        scenario.session_id,
        scenario.emotion,
        scenario.layer,
    )

    baseline_events = _read_emotion_log()
    telemetry.clear()
    captured_events: list[dict] = []
    telemetry_logger = logging.getLogger("abzu.telemetry.audio")
    handler = _TelemetryLogHandler(captured_events)
    telemetry_logger.addHandler(handler)

    if scenario.layer:
        try:
            emotional_state.set_current_layer(scenario.layer)
        except Exception as exc:  # pragma: no cover - defensive guard
            logging.warning("failed to set layer %s: %s", scenario.layer, exc)

    emotional_state.set_last_emotion(scenario.emotion)

    start = _utc_now()

    try:
        raw_audio = Path(tts_coqui.synthesize_speech(scenario.text, scenario.emotion))
        audio_dest = session_dir / "speech.wav"
        shutil.copy2(raw_audio, audio_dest)
        logging.info("%s :: audio synthesized -> %s", scenario.session_id, audio_dest)

        gif_dest = session_dir / "avatar.gif"
        frames = list(avatar_expression_engine.stream_avatar_audio(audio_dest, fps=15))
        if not frames:
            logging.warning(
                "%s :: avatar stream produced no frames; using placeholder",
                scenario.session_id,
            )
            frames = [np.zeros((64, 64, 3), dtype=np.uint8)]
        frame_stack = np.stack(frames).astype(np.uint8)
        gif_bytes = imageio.mimwrite(
            imageio.RETURN_BYTES, frame_stack, format="gif", fps=15
        )
        gif_dest.write_bytes(gif_bytes)
        logging.info("%s :: avatar render saved -> %s", scenario.session_id, gif_dest)

        audio_b64 = audio_dest.with_suffix(audio_dest.suffix + ".b64")
        gif_b64 = gif_dest.with_suffix(gif_dest.suffix + ".b64")
        _write_base64(audio_dest, audio_b64)
        _write_base64(gif_dest, gif_b64)
        audio_dest.unlink(missing_ok=True)
        gif_dest.unlink(missing_ok=True)
    finally:
        telemetry_logger.removeHandler(handler)

    events = captured_events or telemetry.get_events()
    telemetry_path = session_dir / "telemetry.json"
    _write_json(telemetry_path, events)

    after_events = _read_emotion_log()
    new_events = _extract_new_events(baseline_events, after_events)
    emotion_log_path = session_dir / "emotion_stream.jsonl"
    emotion_log_path.write_text(
        "\n".join(new_events) + ("\n" if new_events else ""), encoding="utf-8"
    )

    dropouts = [
        event
        for event in events
        if event.get("status") == "failure"
        or (
            event.get("event") == "audio.play_sound"
            and event.get("status") == "completed"
            and event.get("reason")
        )
        or (event.get("event") == "audio.play_sound" and event.get("reason"))
    ]

    session_summary = {
        "session_id": scenario.session_id,
        "text": scenario.text,
        "emotion": scenario.emotion,
        "layer": scenario.layer,
        "start_utc": start,
        "end_utc": _utc_now(),
        "telemetry_events": len(events),
        "dropouts_detected": len(dropouts),
        "audio_path": str(audio_b64),
        "avatar_path": str(gif_b64),
        "telemetry_path": str(telemetry_path),
        "emotion_log_path": str(emotion_log_path),
    }
    _write_json(session_dir / "summary.json", session_summary)

    logging.info(
        "%s :: telemetry events=%d dropouts=%d",
        scenario.session_id,
        len(events),
        len(dropouts),
    )

    return SessionResult(
        session=scenario,
        start_utc=start,
        end_utc=session_summary["end_utc"],
        audio_path=audio_b64,
        avatar_path=gif_b64,
        telemetry_path=telemetry_path,
        emotion_log_path=emotion_log_path,
        dropouts=dropouts,
    )


def run_demo(output_dir: Path, scenarios: List[Scenario]) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: List[SessionResult] = []
    for scenario in scenarios:
        results.append(run_session(output_dir, scenario))

    bundle_raw = Path(
        shutil.make_archive(str(output_dir / "telemetry_bundle"), "zip", output_dir)
    )
    bundle_b64 = bundle_raw.with_suffix(bundle_raw.suffix + ".b64")
    _write_base64(bundle_raw, bundle_b64)
    bundle_raw.unlink(missing_ok=True)

    summary_payload = {
        "generated_at": _utc_now(),
        "output_dir": str(output_dir),
        "bundle_path": str(bundle_b64),
        "sessions": [
            {
                "session_id": r.session.session_id,
                "emotion": r.session.emotion,
                "layer": r.session.layer,
                "start_utc": r.start_utc,
                "end_utc": r.end_utc,
                "audio_path": str(r.audio_path),
                "avatar_path": str(r.avatar_path),
                "telemetry_path": str(r.telemetry_path),
                "emotion_log_path": str(r.emotion_log_path),
                "dropouts": r.dropouts,
            }
            for r in results
        ],
    }

    _write_json(output_dir / "summary.json", summary_payload)

    md_lines = [
        "# Stage C Demo Rehearsal Summary",
        "",
        f"*Generated:* {summary_payload['generated_at']}",
        f"*Telemetry bundle:* `{summary_payload['bundle_path']}`",
        "",
    ]
    for r in results:
        layer_label = r.session.layer or "n/a"
        md_lines.extend(
            [
                f"## Session {r.session.session_id}",
                "",
                f"- Emotion: **{r.session.emotion}** (layer: {layer_label})",
                f"- Window: {r.start_utc} → {r.end_utc}",
                f"- Audio: `{r.audio_path}`",
                f"- Avatar render: `{r.avatar_path}`",
                f"- Telemetry log: `{r.telemetry_path}`",
                f"- Emotion events: `{r.emotion_log_path}`",
                f"- Dropouts detected: {len(r.dropouts)}",
                "",
            ]
        )
    (output_dir / "summary.md").write_text("\n".join(md_lines), encoding="utf-8")

    return summary_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="logs/stage_c_demo",
        type=Path,
        help="Directory where evidence is stored (default: logs/stage_c_demo)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("abzu.telemetry.audio").setLevel(logging.INFO)

    args = parse_args()

    scenarios = [
        Scenario(
            session_id="session01",
            text="Guardians, confirm the harmonic weave holds steady.",
            emotion="devotion",
            layer="albedo_layer",
        ),
        Scenario(
            session_id="session02",
            text="Initiate the rubedo cadence and sync avatar resonance.",
            emotion="reverence",
            layer="rubedo_layer",
        ),
    ]

    run_demo(args.output, scenarios)


if __name__ == "__main__":
    main()
