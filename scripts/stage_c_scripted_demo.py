#!/usr/bin/env python3
"""Stage C scripted demo harness with telemetry capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import tarfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

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
    stage_b_manifest_entry: dict[str, Any]


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


def _resolve_artifact_url(artifact_uri: str) -> str:
    parsed = urlparse(artifact_uri)
    if parsed.scheme in {"http", "https"}:
        return artifact_uri
    if parsed.scheme in {"", "file"}:
        return Path(parsed.path).resolve().as_uri()
    if parsed.scheme == "evidence":
        base = os.getenv("EVIDENCE_GATEWAY_BASE_URL")
        if not base:
            raise StageBAssetError(
                "Set EVIDENCE_GATEWAY_BASE_URL to fetch evidence:// artifacts "
                "or download the bundle manually."
            )
        prefix = base.rstrip("/")
        joined = f"{parsed.netloc}/{parsed.path.lstrip('/')}" if parsed.netloc else parsed.path.lstrip("/")
        return f"{prefix}/{joined}"
    raise StageBAssetError(
        f"Unsupported artifact URI scheme for Stage B bundle: {artifact_uri}"
    )


def _download_stage_b_bundle(
    artifact_uri: str,
    bundle_name: str,
    download_root: Path,
    expected_sha256: str | None = None,
) -> Path:
    download_root.mkdir(parents=True, exist_ok=True)
    destination = download_root / bundle_name
    if destination.exists():
        if expected_sha256 is None or _sha256(destination) == expected_sha256:
            logger.info("Reusing cached Stage B bundle %s", destination)
            return destination
        logger.warning(
            "Discarding cached Stage B bundle %s due to checksum mismatch",
            destination,
        )
        destination.unlink()
    url = _resolve_artifact_url(artifact_uri)
    logger.info("Downloading Stage B bundle %s -> %s", artifact_uri, destination)
    try:
        with urlopen(url) as response, destination.open("wb") as handle:  # noqa: S310,PTH123
            shutil.copyfileobj(response, handle)
    except URLError as exc:  # pragma: no cover - network failures depend on env
        raise StageBAssetError(
            f"Failed to download Stage B bundle from {artifact_uri}: {exc}"
        ) from exc
    if expected_sha256 is not None:
        checksum = _sha256(destination)
        if checksum != expected_sha256:
            destination.unlink(missing_ok=True)
            raise StageBAssetError(
                "Downloaded Stage B bundle checksum mismatch: "
                f"expected {expected_sha256} but got {checksum}"
            )
    return destination


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
        bundle_info = manifest.get("bundle", {})
        bundle_name = bundle_info.get("name")
        if bundle_name:
            candidate = session_dir / "bundles" / bundle_name
            if candidate.exists():
                bundle_path = candidate
            else:
                artifact_uri = bundle_info.get("artifact_uri")
                if artifact_uri:
                    checksum = bundle_info.get("sha256")
                    download_root = extraction_base / "_bundle_cache"
                    bundle_path = _download_stage_b_bundle(
                        artifact_uri,
                        bundle_name,
                        download_root,
                        expected_sha256=checksum,
                    )
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
        audio_entry = _resolve_media_path(manifest_entry, "audio")
        video_entry = _resolve_media_path(manifest_entry, "video")
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
                audio_rel_path=audio_entry,
                video_rel_path=video_entry,
                audio_duration_s=float(row.get("audio_duration_s", 0.0) or 0.0),
                video_duration_s=float(row.get("video_duration_s", 0.0) or 0.0),
                sync_offset_s=float(row.get("sync_offset_s", 0.0) or 0.0),
                dropout=bool(row.get("dropout", False)),
                source_event=row,
                stage_b_manifest_entry=manifest_entry,
            )
        )
    return steps


def _resolve_media_path(entry: dict[str, Any], media_key: str) -> Path:
    def _path_from_dict(candidate: dict[str, Any]) -> Path | None:
        for key in ("path", "relative_path", "rel_path"):
            value = candidate.get(key)
            if isinstance(value, str) and value:
                return Path(value)
        source = candidate.get("source")
        if isinstance(source, dict):
            result = _path_from_dict(source)
            if result is not None:
                return result
        # Some manifests may wrap assets under variant keys
        for subvalue in candidate.values():
            if isinstance(subvalue, dict):
                result = _path_from_dict(subvalue)
                if result is not None:
                    return result
        return None

    direct = entry.get(f"{media_key}_path")
    if isinstance(direct, str) and direct:
        return Path(direct)

    container = entry.get(media_key)
    if isinstance(container, dict):
        resolved = _path_from_dict(container)
        if resolved is not None:
            return resolved

    assets_container = entry.get("assets")
    if isinstance(assets_container, dict):
        specific = assets_container.get(media_key)
        if isinstance(specific, dict):
            resolved = _path_from_dict(specific)
            if resolved is not None:
                return resolved
    if isinstance(assets_container, list):
        for asset in assets_container:
            if not isinstance(asset, dict):
                continue
            if asset.get("kind") == media_key or asset.get("type") == media_key:
                resolved = _path_from_dict(asset)
                if resolved is not None:
                    return resolved

    raise StageBAssetError(
        f"Media manifest entry for step {entry.get('step_id')} missing {media_key} path"
    )


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
    copy_media: bool = False,
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
    audio_assets: list[dict[str, Any]] = []
    video_assets: list[dict[str, Any]] = []
    max_sync_offset = 0.0
    dropouts_detected = False

    bundle_info = stage_b_session.manifest.get("bundle", {})

    def _record_asset(
        source_path: Path,
        *,
        source_rel: Path,
        dest_rel: Path | None = None,
        include_bundle: bool = False,
    ) -> dict[str, Any]:
        if not source_path.is_file():
            raise StageBAssetError(f"Required Stage B asset missing: {source_path}")
        stat = source_path.stat()
        metadata: dict[str, Any] = {
            "source_path": str(source_rel),
            "size_bytes": stat.st_size,
            "sha256": _sha256(source_path),
            "available_locally": False,
        }
        if include_bundle and bundle_info:
            if "artifact_uri" in bundle_info:
                metadata["bundle_uri"] = bundle_info["artifact_uri"]
            if "sha256" in bundle_info:
                metadata["bundle_sha256"] = bundle_info["sha256"]
            if "name" in bundle_info:
                metadata["bundle_name"] = bundle_info["name"]
            if "size_bytes" in bundle_info:
                metadata["bundle_size_bytes"] = bundle_info["size_bytes"]
            metadata["bundle_member"] = str(source_rel)
        if copy_media:
            destination = output_dir / (dest_rel or source_rel)
            copied = _copy_file(
                source_path,
                destination,
                output_root=output_dir,
                source_rel=source_rel,
            )
            metadata["path"] = str(copied.destination_rel)
            metadata["available_locally"] = True
        return metadata

    for step in stage_b_session.steps:
        logger.info(
            '[%s] prompt="%s" emotion=%s', step.step_id, step.prompt, step.emotion
        )
        audio_meta = _record_asset(
            stage_b_session.data_root / step.audio_rel_path,
            source_rel=step.audio_rel_path,
            dest_rel=step.audio_rel_path,
            include_bundle=True,
        )
        video_meta = _record_asset(
            stage_b_session.data_root / step.video_rel_path,
            source_rel=step.video_rel_path,
            dest_rel=step.video_rel_path,
            include_bundle=True,
        )
        audio_assets.append(audio_meta)
        video_assets.append(video_meta)
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
        entry = deepcopy(step.stage_b_manifest_entry)
        entry.setdefault("step_id", step.step_id)
        entry.setdefault("prompt", step.prompt)
        entry.setdefault("emotion", step.emotion)
        entry.setdefault("timestamp", step.timestamp)
        source_block = {
            "stage": stage_b_session.stage,
            "run_id": stage_b_session.run_id,
            "session": stage_b_session.session_id,
            "audio_path": str(step.audio_rel_path),
            "video_path": str(step.video_rel_path),
        }
        if "artifact_uri" in bundle_info:
            source_block["bundle_uri"] = bundle_info["artifact_uri"]
        if "sha256" in bundle_info:
            source_block["bundle_sha256"] = bundle_info["sha256"]
        if "name" in bundle_info:
            source_block["bundle_name"] = bundle_info["name"]
        entry["stage_c"] = {
            "prompt": step.prompt,
            "emotion": step.emotion,
            "timestamp": step.timestamp,
            "telemetry": {
                "audio_duration_s": round(step.audio_duration_s, 3),
                "video_duration_s": round(step.video_duration_s, 3),
                "sync_offset_s": round(step.sync_offset_s, 3),
                "dropout": step.dropout,
                "event_sha256": _hash_json(step.source_event),
            },
            "assets": {
                "audio": deepcopy(audio_meta),
                "video": deepcopy(video_meta),
            },
            "source": source_block,
            "media_copy_enabled": copy_media,
        }
        media_manifest_entries.append(entry)

    emotion_rows = _read_jsonl(stage_b_session.emotion_path)
    emotion_meta = _record_asset(
        stage_b_session.emotion_path,
        source_rel=Path("emotion/stream.jsonl"),
        dest_rel=Path("emotion/stream.jsonl"),
        include_bundle=True,
    )
    stage_b_events_meta = _record_asset(
        stage_b_session.events_path,
        source_rel=Path("telemetry/events.jsonl"),
        dest_rel=Path("telemetry/stage_b_events.jsonl"),
        include_bundle=True,
    )
    stage_b_media_manifest_meta = _record_asset(
        stage_b_session.media_manifest_path,
        source_rel=Path("telemetry/media_manifest.json"),
        dest_rel=Path("telemetry/stage_b_media_manifest.json"),
        include_bundle=True,
    )
    stage_b_session_manifest_meta = _record_asset(
        stage_b_session.manifest_path,
        source_rel=Path(stage_b_session.manifest_path.name),
        dest_rel=Path("telemetry/stage_b_session_manifest.json"),
        include_bundle=False,
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
            "manifest_sha256": stage_b_session_manifest_meta["sha256"],
            "bundle": stage_b_session.manifest.get("bundle", {}),
            "assets": {
                "audio_files": len(audio_assets),
                "audio_bytes": sum(asset["size_bytes"] for asset in audio_assets),
                "audio_available_locally": copy_media,
                "video_files": len(video_assets),
                "video_bytes": sum(asset["size_bytes"] for asset in video_assets),
                "video_available_locally": copy_media,
                "emotion_stream": {
                    **emotion_meta,
                    "samples": len(emotion_rows),
                },
                "telemetry_events": stage_b_events_meta,
                "telemetry_media_manifest": stage_b_media_manifest_meta,
            },
        },
        "replay": {
            "events_path": str(telemetry_path.relative_to(output_dir)),
            "events_sha256": stage_c_events_sha,
            "media_manifest_path": str(manifest_path.relative_to(output_dir)),
            "media_manifest_sha256": stage_c_media_manifest_sha,
        },
        "configuration": {"copy_media": copy_media},
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
    parser.add_argument(
        "--copy-media",
        action="store_true",
        help=(
            "Copy Stage B audio/video assets into the Stage C output directory. "
            "When omitted, the run emits provenance pointing at the Stage B bundle."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        help=(
            "Deterministic seed used by higher-level launchers; "
            "accepted for compatibility even when no randomization is required."
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
            copy_media=args.copy_media,
        )
    except StageBAssetError as exc:
        logger.error("Stage B asset resolution failed: %s", exc)
        raise SystemExit(1) from exc

    summary_path = args.output_dir / "telemetry" / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
