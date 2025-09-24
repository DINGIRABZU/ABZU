#!/usr/bin/env python3
"""Stage C scripted demo harness with telemetry capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoStep:
    """Single scripted beat sourced from Stage B telemetry."""

    step_id: str
    prompt: str
    emotion: str
    timestamp: str
    audio_rel_path: Path
    video_rel_path: Path
    audio_duration_s: float
    video_duration_s: float
    sync_offset_s: float
    dropout: bool
    source_event: dict[str, Any]


@dataclass
class StageBSession:
    """Resolved Stage B rehearsal metadata."""

    run_id: str
    session_id: str
    stage: str
    manifest_path: Path
    manifest: dict[str, Any]
    data_root: Path
    steps: list[DemoStep]
    events_path: Path
    media_manifest_path: Path
    emotion_path: Path


@dataclass
class CopiedFile:
    """Metadata describing a copied Stage B asset."""

    source: Path
    destination: Path
    destination_rel: Path
    source_rel: Path
    size_bytes: int
    sha256: str


class StageBAssetError(RuntimeError):
    """Raised when Stage B rehearsal assets cannot be resolved."""


REQUIRED_DATA_PATHS: Sequence[Path] = (
    Path("audio"),
    Path("video"),
    Path("emotion/stream.jsonl"),
    Path("telemetry/events.jsonl"),
    Path("telemetry/media_manifest.json"),
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:  # noqa: PTH123
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_json(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _has_required_assets(base: Path) -> bool:
    missing: list[str] = []
    audio_dir = base / "audio"
    if not (audio_dir.is_dir() and any(audio_dir.iterdir())):
        missing.append("audio")
    video_dir = base / "video"
    if not (video_dir.is_dir() and any(video_dir.iterdir())):
        missing.append("video")
    if not (base / "emotion" / "stream.jsonl").is_file():
        missing.append("emotion/stream.jsonl")
    if not (base / "telemetry" / "events.jsonl").is_file():
        missing.append("telemetry/events.jsonl")
    if not (base / "telemetry" / "media_manifest.json").is_file():
        missing.append("telemetry/media_manifest.json")
    if missing:
        logger.debug(
            "Stage B asset root %s missing required members: %s",
            base,
            ", ".join(missing),
        )
        return False
    return True


def _safe_extract(archive: tarfile.TarFile, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    root = target_dir.resolve()
    for member in archive.getmembers():
        member_path = (target_dir / member.name).resolve()
        if not str(member_path).startswith(str(root)):
            raise StageBAssetError(
                f"Bundle member {member.name} escapes extraction root {root}"
            )
        archive.extract(member, target_dir)


def _extract_bundle(bundle_path: Path, target_dir: Path) -> Path:
    if _has_required_assets(target_dir):
        return target_dir
    logger.info("Extracting Stage B bundle %s -> %s", bundle_path, target_dir)
    with tarfile.open(bundle_path, "r:gz") as archive:
        _safe_extract(archive, target_dir)
    if not _has_required_assets(target_dir):
        raise StageBAssetError(
            "Extracted Stage B bundle "
            f"{bundle_path} but required assets are missing in {target_dir}"
        )
    return target_dir


def _locate_stage_b_assets(
    manifest_path: Path,
    manifest: dict[str, Any],
    assets_override: Path | None,
    bundle_override: Path | None,
    extraction_base: Path,
) -> Path:
    candidates: list[Path] = []
    if assets_override is not None:
        candidates.append(assets_override)
    session_dir = manifest_path.parent
    candidates.append(session_dir)
    bundle_path: Path | None = None
    if bundle_override is not None:
        bundle_path = bundle_override
    else:
        bundle_name = manifest.get("bundle", {}).get("name")
        if bundle_name:
            candidate = session_dir / "bundles" / bundle_name
            if candidate.exists():
                bundle_path = candidate
    if bundle_path is not None:
        extraction_root = (
            extraction_base
            / str(manifest.get("run_id", session_dir.parent.name))
            / str(manifest.get("session", session_dir.name))
        )
        candidates.append(_extract_bundle(bundle_path, extraction_root))
    for candidate in candidates:
        if candidate and _has_required_assets(candidate):
            logger.info("Using Stage B asset root %s", candidate)
            return candidate
    raise StageBAssetError(
        "Unable to locate Stage B rehearsal assets. "
        "Provide --stage-b-assets or --stage-b-bundle pointing to the extracted media."
    )


def _build_steps(
    events_rows: list[dict[str, Any]],
    media_manifest: list[dict[str, Any]],
) -> list[DemoStep]:
    manifest_by_step = {
        entry["step_id"]: entry for entry in media_manifest if "step_id" in entry
    }
    steps: list[DemoStep] = []
    for row in events_rows:
        step_id = row.get("step_id")
        if not step_id:
            raise StageBAssetError("Stage B events payload missing step_id")
        manifest_entry = manifest_by_step.get(step_id)
        if not manifest_entry:
            raise StageBAssetError(f"No media manifest entry found for step {step_id}")
        audio_entry = manifest_entry.get("audio_path")
        video_entry = manifest_entry.get("video_path")
        if not audio_entry or not video_entry:
            raise StageBAssetError(
                f"Media manifest entry for step {step_id} missing audio/video paths"
            )
        prompt = row.get("prompt") or manifest_entry.get("prompt") or step_id
        emotion = row.get("emotion", "")
        timestamp = row.get("timestamp")
        if timestamp is None:
            raise StageBAssetError(f"Stage B event for {step_id} missing timestamp")
        steps.append(
            DemoStep(
                step_id=step_id,
                prompt=prompt,
                emotion=emotion,
                timestamp=timestamp,
                audio_rel_path=Path(audio_entry),
                video_rel_path=Path(video_entry),
                audio_duration_s=float(row.get("audio_duration_s", 0.0) or 0.0),
                video_duration_s=float(row.get("video_duration_s", 0.0) or 0.0),
                sync_offset_s=float(row.get("sync_offset_s", 0.0) or 0.0),
                dropout=bool(row.get("dropout", False)),
                source_event=row,
            )
        )
    return steps


def _copy_file(
    source: Path,
    destination: Path,
    *,
    output_root: Path,
    source_rel: Path,
) -> CopiedFile:
    if not source.is_file():
        raise StageBAssetError(f"Required Stage B asset missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    size_bytes = destination.stat().st_size
    sha = _sha256(destination)
    return CopiedFile(
        source=source,
        destination=destination,
        destination_rel=destination.relative_to(output_root),
        source_rel=source_rel,
        size_bytes=size_bytes,
        sha256=sha,
    )


def _load_stage_b_session(
    manifest_path: Path,
    *,
    assets_override: Path | None,
    bundle_override: Path | None,
    extraction_base: Path,
) -> StageBSession:
    if not manifest_path.is_file():
        raise StageBAssetError(f"Stage B session manifest not found at {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_root = _locate_stage_b_assets(
        manifest_path,
        manifest,
        assets_override,
        bundle_override,
        extraction_base,
    )
    events_path = data_root / "telemetry" / "events.jsonl"
    media_manifest_path = data_root / "telemetry" / "media_manifest.json"
    emotion_path = data_root / "emotion" / "stream.jsonl"
    events_rows = _read_jsonl(events_path)
    media_manifest = json.loads(media_manifest_path.read_text(encoding="utf-8"))
    if not isinstance(media_manifest, list):
        raise StageBAssetError(
            f"Unexpected media manifest format at {media_manifest_path}: expected list"
        )
    steps = _build_steps(events_rows, media_manifest)
    return StageBSession(
        run_id=str(manifest.get("run_id", manifest_path.parent.parent.name)),
        session_id=str(manifest.get("session", manifest_path.parent.name)),
        stage=str(manifest.get("stage", "stage_b")),
        manifest_path=manifest_path,
        manifest=manifest,
        data_root=data_root,
        steps=steps,
        events_path=events_path,
        media_manifest_path=media_manifest_path,
        emotion_path=emotion_path,
    )


def _resolve_stage_b_run(run_arg: str | Path) -> Path:
    candidate = Path(run_arg)
    if candidate.exists():
        return candidate
    default = Path("logs") / "stage_b" / str(run_arg)
    if default.exists():
        return default
    raise StageBAssetError(f"Stage B run directory not found for {run_arg}")


def run_session(
    output_dir: Path,
    *,
    stage_b_manifest: Path,
    stage_b_assets: Path | None = None,
    stage_b_bundle: Path | None = None,
    bundle_extract_dir: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if stage_b_assets is not None and not stage_b_assets.exists():
        raise StageBAssetError(f"Stage B asset directory not found: {stage_b_assets}")
    if stage_b_bundle is not None and not stage_b_bundle.exists():
        raise StageBAssetError(f"Stage B bundle not found: {stage_b_bundle}")
    extraction_base = bundle_extract_dir or (output_dir / "_stage_b_assets")
    stage_b_session = _load_stage_b_session(
        stage_b_manifest,
        assets_override=stage_b_assets,
        bundle_override=stage_b_bundle,
        extraction_base=extraction_base,
    )

    logger.info(
        "Starting Stage C scripted demo replay from Stage B run %s session %s",
        stage_b_session.run_id,
        stage_b_session.session_id,
    )

    telemetry_rows: list[dict[str, Any]] = []
    media_manifest_entries: list[dict[str, Any]] = []
    audio_assets: list[CopiedFile] = []
    video_assets: list[CopiedFile] = []
    max_sync_offset = 0.0
    dropouts_detected = False

    for step in stage_b_session.steps:
        logger.info(
            '[%s] prompt="%s" emotion=%s', step.step_id, step.prompt, step.emotion
        )
        audio_copy = _copy_file(
            stage_b_session.data_root / step.audio_rel_path,
            output_dir / step.audio_rel_path,
            output_root=output_dir,
            source_rel=step.audio_rel_path,
        )
        video_copy = _copy_file(
            stage_b_session.data_root / step.video_rel_path,
            output_dir / step.video_rel_path,
            output_root=output_dir,
            source_rel=step.video_rel_path,
        )
        audio_assets.append(audio_copy)
        video_assets.append(video_copy)
        max_sync_offset = max(max_sync_offset, abs(step.sync_offset_s))
        dropouts_detected = dropouts_detected or step.dropout
        telemetry_rows.append(
            {
                "timestamp": step.timestamp,
                "event": "stage_c.demo.step",
                "step_id": step.step_id,
                "emotion": step.emotion,
                "audio_duration_s": round(step.audio_duration_s, 3),
                "video_duration_s": round(step.video_duration_s, 3),
                "sync_offset_s": round(step.sync_offset_s, 3),
                "dropout": step.dropout,
                "prompt": step.prompt,
                "source": {
                    "stage": stage_b_session.stage,
                    "run_id": stage_b_session.run_id,
                    "session": stage_b_session.session_id,
                    "event_sha256": _hash_json(step.source_event),
                },
            }
        )
        media_manifest_entries.append(
            {
                "step_id": step.step_id,
                "prompt": step.prompt,
                "emotion": step.emotion,
                "timestamp": step.timestamp,
                "audio_path": str(audio_copy.destination_rel),
                "video_path": str(video_copy.destination_rel),
                "source": {
                    "stage": stage_b_session.stage,
                    "run_id": stage_b_session.run_id,
                    "session": stage_b_session.session_id,
                    "audio": {
                        "path": str(audio_copy.source_rel),
                        "sha256": audio_copy.sha256,
                        "size_bytes": audio_copy.size_bytes,
                    },
                    "video": {
                        "path": str(video_copy.source_rel),
                        "sha256": video_copy.sha256,
                        "size_bytes": video_copy.size_bytes,
                    },
                    "event_sha256": _hash_json(step.source_event),
                },
            }
        )

    emotion_rows = _read_jsonl(stage_b_session.emotion_path)
    emotion_copy = _copy_file(
        stage_b_session.emotion_path,
        output_dir / "emotion" / "stream.jsonl",
        output_root=output_dir,
        source_rel=Path("emotion/stream.jsonl"),
    )
    stage_b_events_copy = _copy_file(
        stage_b_session.events_path,
        output_dir / "telemetry" / "stage_b_events.jsonl",
        output_root=output_dir,
        source_rel=Path("telemetry/events.jsonl"),
    )
    stage_b_media_manifest_copy = _copy_file(
        stage_b_session.media_manifest_path,
        output_dir / "telemetry" / "stage_b_media_manifest.json",
        output_root=output_dir,
        source_rel=Path("telemetry/media_manifest.json"),
    )
    stage_b_session_manifest_copy = _copy_file(
        stage_b_session.manifest_path,
        output_dir / "telemetry" / "stage_b_session_manifest.json",
        output_root=output_dir,
        source_rel=Path(stage_b_session.manifest_path.name),
    )

    telemetry_path = output_dir / "telemetry" / "events.jsonl"
    _write_jsonl(telemetry_path, telemetry_rows)
    stage_c_events_sha = _sha256(telemetry_path)

    manifest_path = output_dir / "telemetry" / "media_manifest.json"
    manifest_path.write_text(
        json.dumps(media_manifest_entries, indent=2) + "\n", encoding="utf-8"
    )
    stage_c_media_manifest_sha = _sha256(manifest_path)

    summary = {
        "timestamp": _timestamp(),
        "steps": len(stage_b_session.steps),
        "max_sync_offset_s": round(max_sync_offset, 3),
        "dropouts_detected": dropouts_detected,
        "source": {
            "stage": stage_b_session.stage,
            "run_id": stage_b_session.run_id,
            "session": stage_b_session.session_id,
            "manifest_path": str(stage_b_session.manifest_path),
            "manifest_sha256": stage_b_session_manifest_copy.sha256,
            "bundle": stage_b_session.manifest.get("bundle", {}),
            "assets": {
                "audio_files": len(audio_assets),
                "audio_bytes": sum(asset.size_bytes for asset in audio_assets),
                "video_files": len(video_assets),
                "video_bytes": sum(asset.size_bytes for asset in video_assets),
                "emotion_stream": {
                    "path": str(emotion_copy.destination_rel),
                    "source_path": str(emotion_copy.source_rel),
                    "sha256": emotion_copy.sha256,
                    "size_bytes": emotion_copy.size_bytes,
                    "samples": len(emotion_rows),
                },
                "telemetry_events": {
                    "path": str(stage_b_events_copy.destination_rel),
                    "source_path": str(stage_b_events_copy.source_rel),
                    "sha256": stage_b_events_copy.sha256,
                    "size_bytes": stage_b_events_copy.size_bytes,
                },
                "telemetry_media_manifest": {
                    "path": str(stage_b_media_manifest_copy.destination_rel),
                    "source_path": str(stage_b_media_manifest_copy.source_rel),
                    "sha256": stage_b_media_manifest_copy.sha256,
                    "size_bytes": stage_b_media_manifest_copy.size_bytes,
                },
            },
        },
        "replay": {
            "events_path": str(telemetry_path.relative_to(output_dir)),
            "events_sha256": stage_c_events_sha,
            "media_manifest_path": str(manifest_path.relative_to(output_dir)),
            "media_manifest_sha256": stage_c_media_manifest_sha,
        },
    }

    telemetry_summary_path = output_dir / "telemetry" / "summary.json"
    telemetry_summary_path.write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    logger.info(
        "Session complete: %s steps replayed from Stage B run %s/%s "
        "(max sync offset %.3fs)",
        len(stage_b_session.steps),
        stage_b_session.run_id,
        stage_b_session.session_id,
        round(max_sync_offset, 3),
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="Directory for session evidence")
    parser.add_argument(
        "--stage-b-run",
        default="logs/stage_b/20250921T230434Z",
        help="Stage B run ID or path containing rehearsal sessions.",
    )
    parser.add_argument(
        "--stage-b-session",
        default="session_01",
        help=(
            "Stage B session identifier to replay "
            "(ignored when --stage-b-manifest is provided)."
        ),
    )
    parser.add_argument(
        "--stage-b-manifest",
        type=Path,
        help=(
            "Path to a Stage B session_manifest.json "
            "(overrides --stage-b-run/--stage-b-session)."
        ),
    )
    parser.add_argument(
        "--stage-b-assets",
        type=Path,
        help=(
            "Directory containing extracted Stage B assets "
            "(audio/video/emotion/telemetry)."
        ),
    )
    parser.add_argument(
        "--stage-b-bundle",
        type=Path,
        help=(
            "Optional Stage B bundle (.tar.gz) to extract "
            "when assets are not present locally."
        ),
    )
    parser.add_argument(
        "--bundle-extract-dir",
        type=Path,
        help=(
            "Directory used to extract Stage B bundles "
            "(defaults to <output>/_stage_b_assets)."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        if args.stage_b_manifest is not None:
            manifest_path = args.stage_b_manifest
        else:
            run_path = _resolve_stage_b_run(args.stage_b_run)
            manifest_path = (
                run_path / "rehearsals" / args.stage_b_session / "session_manifest.json"
            )
    except StageBAssetError as exc:
        parser.error(str(exc))
        return

    try:
        summary = run_session(
            args.output_dir,
            stage_b_manifest=manifest_path,
            stage_b_assets=args.stage_b_assets,
            stage_b_bundle=args.stage_b_bundle,
            bundle_extract_dir=args.bundle_extract_dir,
        )
    except StageBAssetError as exc:
        logger.error("Stage B asset resolution failed: %s", exc)
        raise SystemExit(1) from exc

    summary_path = args.output_dir / "telemetry" / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
