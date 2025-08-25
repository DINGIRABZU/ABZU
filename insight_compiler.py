from __future__ import annotations

"""Aggregate interaction logs into an insight matrix."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

INSIGHT_FILE = Path(__file__).resolve().parent / "insight_matrix.json"
INSIGHT_MANIFEST_FILE = Path(__file__).resolve().parent / "insight_manifest.json"

# Map ritual glyphs to intents
_INTENT_FILE = Path(__file__).resolve().parent / "intent_matrix.json"
try:
    _INTENT_MAP: Dict[str, Dict[str, Any]] = json.loads(
        _INTENT_FILE.read_text(encoding="utf-8")
    )
except Exception:  # pragma: no cover - file may be missing
    _INTENT_MAP = {}

_GLYPHS: Dict[str, set[str]] = {}
for _name, _info in _INTENT_MAP.items():
    for _g in _info.get("glyphs", []):
        _GLYPHS.setdefault(_name, set()).add(_g)


def load_insights() -> Dict[str, Any]:
    """Return the current insight matrix as a dictionary."""
    if INSIGHT_FILE.exists():
        try:
            return json.loads(INSIGHT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _bump_version(version: str) -> str:
    """Return the next patch semantic version."""
    try:
        major, minor, patch = map(int, version.split("."))
    except Exception:  # pragma: no cover - invalid stored version
        return "0.1.0"
    patch += 1
    return f"{major}.{minor}.{patch}"


def _update_manifest(now: str) -> None:
    """Write a companion manifest tagging insight updates with version and checksums."""

    def _checksum(path: Path) -> str:
        import hashlib

        return hashlib.sha256(path.read_bytes()).hexdigest()

    checksums = {}
    if INSIGHT_FILE.exists():
        checksums["insight_matrix"] = _checksum(INSIGHT_FILE)
    if _INTENT_FILE.exists():
        checksums["intent_matrix"] = _checksum(_INTENT_FILE)

    manifest: Dict[str, Any] = {
        "version": "0.1.0",
        "updated": "",
        "checksums": checksums,
        "history": [],
    }
    if INSIGHT_MANIFEST_FILE.exists():
        try:
            manifest = json.loads(INSIGHT_MANIFEST_FILE.read_text(encoding="utf-8"))
            manifest["history"] = manifest.get("history", [])
            manifest["version"] = _bump_version(manifest.get("version", "0.1.0"))
        except Exception:  # pragma: no cover - malformed manifest
            manifest = {
                "version": "0.1.0",
                "updated": "",
                "checksums": checksums,
                "history": [],
            }

    manifest["updated"] = now
    manifest["checksums"] = checksums
    manifest.setdefault("history", [])
    manifest["history"].append(
        {"version": manifest["version"], "updated": now, "checksums": checksums}
    )
    INSIGHT_MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _broadcast_scores(scores: Dict[str, Any]) -> None:
    """Send archetypal scores to a webhook or message queue if configured."""
    webhook = os.getenv("ARCHETYPE_SCORE_WEBHOOK_URL")
    queue_path = os.getenv("ARCHETYPE_SCORE_QUEUE_PATH")
    if webhook:
        try:
            requests.post(webhook, json=scores, timeout=3)
        except Exception:  # pragma: no cover - network failure is non-critical
            pass
    if queue_path:
        try:
            with open(queue_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(scores) + "\n")
        except Exception:  # pragma: no cover - queue path may be invalid
            pass


def update_insights(log_entries: List[dict]) -> None:
    """Update insight matrix using ``log_entries`` records."""
    insights = load_insights()
    now = datetime.utcnow().isoformat()

    for entry in log_entries:
        pattern = entry.get("intent")
        if not pattern:
            continue
        tone = entry.get("tone") or "neutral"
        success = bool(entry.get("success"))
        info = insights.setdefault(
            pattern,
            {
                "counts": {
                    "total": 0,
                    "success": 0,
                    "tones": {},
                    "emotions": {},
                    "responded_with": {},
                },
                "resonance_index": {},
            },
        )
        counts = info["counts"]
        counts["total"] += 1
        if success:
            counts["success"] += 1
        tone_ct = counts["tones"].setdefault(tone, {"total": 0, "success": 0})
        tone_ct["total"] += 1
        if success:
            tone_ct["success"] += 1

        emotion = entry.get("emotion")
        if emotion:
            emo_ct = counts["emotions"].setdefault(emotion, {"total": 0, "success": 0})
            emo_ct["total"] += 1
            if success:
                emo_ct["success"] += 1

        responded = entry.get("responded_with")
        if responded is None and isinstance(entry.get("result"), dict):
            responded = [
                k.replace("_path", "")
                for k in entry["result"].keys()
                if k in {"text", "voice_path", "music_path"}
            ]
        if isinstance(responded, str):
            responded = [responded]
        if responded:
            for r in responded:
                counts["responded_with"][r] = counts["responded_with"].get(r, 0) + 1

        # Detect ritual glyphs for resonance tracking
        if emotion:
            glyphs = _GLYPHS.get(pattern, set())
            if glyphs:
                serialized = json.dumps(entry, ensure_ascii=False)
                if any(g in serialized for g in glyphs):
                    res_idx = info.setdefault("resonance_index", {})
                    res_idx[emotion] = res_idx.get(emotion, 0) + 1

    for pattern, info in insights.items():
        counts = info.get("counts", {})
        total = counts.get("total", 0)
        succ = counts.get("success", 0)
        best_tone = ""
        best_rate = -1.0
        for tone, vals in counts.get("tones", {}).items():
            t_total = vals.get("total", 0)
            if t_total:
                rate = vals.get("success", 0) / t_total
                if rate > best_rate:
                    best_rate = rate
                    best_tone = tone
        info["best_tone"] = best_tone
        info["action_success_rate"] = round(succ / total, 3) if total else 0.0
        info["last_updated"] = now

    INSIGHT_FILE.write_text(json.dumps(insights, indent=2), encoding="utf-8")
    _update_manifest(now)

    scores = {
        pattern: {
            "action_success_rate": info.get("action_success_rate", 0.0),
            "best_tone": info.get("best_tone", ""),
            "resonance_index": info.get("resonance_index", {}),
        }
        for pattern, info in insights.items()
    }
    _broadcast_scores(scores)


__all__ = ["update_insights", "load_insights", "INSIGHT_FILE", "INSIGHT_MANIFEST_FILE"]
