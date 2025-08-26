"""Tests for insight compiler."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
import hashlib
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import insight_compiler as ic  # noqa: E402
import logging_filters  # noqa: E402


def test_update_aggregates(tmp_path, monkeypatch):
    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    logs = [
        {
            "intent": "open portal",
            "tone": "joy",
            "emotion": "joy",
            "responded_with": "text",
            "success": True,
        },
        {
            "intent": "open portal",
            "tone": "joy",
            "emotion": "sad",
            "responded_with": "voice",
            "success": False,
        },
    ]
    ic.update_insights(logs)
    data = json.loads(insight_file.read_text())
    assert data["open portal"]["counts"]["total"] == 2
    assert data["open portal"]["counts"]["success"] == 1
    assert data["open portal"]["counts"]["emotions"]["joy"]["total"] == 1
    assert data["open portal"]["counts"]["emotions"]["sad"]["total"] == 1
    assert data["open portal"]["counts"]["responded_with"]["text"] == 1
    assert data["open portal"]["counts"]["responded_with"]["voice"] == 1

    logs2 = [
        {
            "intent": "open portal",
            "tone": "calm",
            "emotion": "joy",
            "responded_with": ["text", "music"],
            "success": True,
        },
    ]
    ic.update_insights(logs2)
    data = json.loads(insight_file.read_text())
    assert data["open portal"]["counts"]["total"] == 3
    assert data["open portal"]["counts"]["success"] == 2
    assert data["open portal"]["counts"]["emotions"]["joy"]["total"] == 2
    assert data["open portal"]["counts"]["emotions"]["joy"]["success"] == 2
    assert data["open portal"]["counts"]["responded_with"]["text"] == 2
    assert data["open portal"]["counts"]["responded_with"]["voice"] == 1
    assert data["open portal"]["counts"]["responded_with"]["music"] == 1
    assert data["open portal"]["best_tone"] == "calm"
    assert abs(data["open portal"]["action_success_rate"] - 2 / 3) < 0.001


def test_resonance_index_increases(tmp_path, monkeypatch):
    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    log = {
        "intent": "conjure fire",
        "tone": "joy",
        "emotion": "joy",
        "text": "ignite \U0001f702",
        "success": True,
    }

    ic.update_insights([log])
    data = json.loads(insight_file.read_text())
    assert data["conjure fire"]["resonance_index"]["joy"] == 1

    ic.update_insights([log])
    data = json.loads(insight_file.read_text())
    assert data["conjure fire"]["resonance_index"]["joy"] == 2


def test_manifest_version_bumps(tmp_path, monkeypatch):
    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    # seed manifest with starting version
    manifest_file.write_text(json.dumps({"version": "0.1.0", "updated": ""}))
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    log = {"intent": "open portal", "tone": "calm", "success": True}
    ic.update_insights([log])
    manifest = json.loads(manifest_file.read_text())
    assert manifest["version"] == "0.1.1"
    first_time = manifest["updated"]
    checksum = hashlib.sha256(insight_file.read_bytes()).hexdigest()
    assert manifest["checksums"]["insight_matrix"] == checksum
    assert "intent_matrix" in manifest["checksums"]
    mirror_checksum = hashlib.sha256((ROOT / "mirror_thresholds.json").read_bytes()).hexdigest()
    assert manifest["checksums"]["mirror_thresholds"] == mirror_checksum
    assert manifest["semantic_versions"]["insight_matrix"] == "0.1.0"

    ic.update_insights([log])
    manifest = json.loads(manifest_file.read_text())
    assert manifest["version"] == "0.1.2"
    assert manifest["updated"] != first_time
    checksum2 = hashlib.sha256(insight_file.read_bytes()).hexdigest()
    assert manifest["checksums"]["insight_matrix"] == checksum2
    assert manifest["semantic_versions"]["insight_matrix"] == "0.1.1"


def test_manifest_history_records_updates(tmp_path, monkeypatch):
    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    log = {"intent": "open portal", "tone": "calm", "success": True}
    ic.update_insights([log])
    manifest = json.loads(manifest_file.read_text())
    first_checksum = hashlib.sha256(insight_file.read_bytes()).hexdigest()
    assert manifest["history"][0]["version"] == "0.1.0"
    assert manifest["history"][0]["updated"]
    assert manifest["history"][0]["checksums"]["insight_matrix"] == first_checksum
    assert manifest["history"][0]["semantic_versions"]["insight_matrix"] == "0.1.0"

    ic.update_insights([log])
    manifest = json.loads(manifest_file.read_text())
    second_checksum = hashlib.sha256(insight_file.read_bytes()).hexdigest()
    assert [h["version"] for h in manifest["history"]] == ["0.1.0", "0.1.1"]
    assert manifest["version"] == "0.1.1"
    assert manifest["history"][1]["checksums"]["insight_matrix"] == second_checksum
    assert manifest["history"][1]["semantic_versions"]["insight_matrix"] == "0.1.1"


def test_connector_invoked(tmp_path, monkeypatch):
    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    called: dict = {}

    def fake_post(
        url, json, headers=None, timeout=3
    ):  # noqa: A002 - match requests signature
        called["url"] = url
        called["json"] = json
        called["headers"] = headers
        called["timeout"] = timeout
        return object()

    monkeypatch.setenv("ARCHETYPE_SCORE_WEBHOOK_URL", "http://example.com")
    monkeypatch.setenv("ARCHETYPE_SCORE_WEBHOOK_HEADERS", json.dumps({"X-Test": "1"}))
    monkeypatch.setattr(ic.requests, "post", fake_post)

    logs = [
        {
            "intent": "open portal",
            "tone": "joy",
            "emotion": "joy",
            "responded_with": "text",
            "success": True,
        }
    ]
    ic.update_insights(logs)

    assert called["url"] == "http://example.com"
    assert "open portal" in called["json"]
    assert "action_success_rate" in called["json"]["open portal"]
    assert called["headers"] == {"X-Test": "1"}


def test_logging_filter_integration(tmp_path, monkeypatch, caplog):
    """Log records enriched by the emotion filter update the matrix."""
    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    logging_filters.set_emotion_provider(lambda: ("joy", 0.8))
    logger = logging.getLogger("insight-test")
    logger.addFilter(logging_filters.EmotionFilter())

    with caplog.at_level(logging.INFO):
        logger.info(
            "spell cast",
            extra={
                "intent": "open portal",
                "tone": "calm",
                "responded_with": "text",
                "success": True,
            },
        )

    record = caplog.records[0]
    assert record.emotion == "joy"
    entry = {
        "intent": record.intent,
        "tone": record.tone,
        "emotion": record.emotion,
        "responded_with": record.responded_with,
        "success": record.success,
    }
    ic.update_insights([entry])
    data = json.loads(insight_file.read_text())
    assert data["open portal"]["counts"]["emotions"]["joy"]["total"] == 1
    assert data["open portal"]["counts"]["total"] == 1


def test_broadcast_scores_handles_errors(monkeypatch, tmp_path):
    """_broadcast_scores should ignore webhook and queue failures."""

    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    logs = [{"intent": "open portal", "tone": "joy", "success": True}]

    # Webhook error
    monkeypatch.setenv("ARCHETYPE_SCORE_WEBHOOK_URL", "http://example.com")
    monkeypatch.setattr(
        ic.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    # Queue path error (non-existent directory)
    monkeypatch.setenv("ARCHETYPE_SCORE_QUEUE_PATH", str(tmp_path / "no" / "queue.log"))

    ic.update_insights(logs)  # Should not raise despite errors


def test_json_files_match_schema():
    files = [
        ("insight_matrix.json", "insight_matrix.schema.json"),
        ("intent_matrix.json", "intent_matrix.schema.json"),
        ("mirror_thresholds.json", "mirror_thresholds.schema.json"),
        ("insight_manifest.json", "insight_manifest.schema.json"),
    ]
    for json_name, schema_name in files:
        data = json.loads((ROOT / json_name).read_text())
        schema = json.loads((ROOT / "schemas" / schema_name).read_text())
        jsonschema.validate(data, schema)
