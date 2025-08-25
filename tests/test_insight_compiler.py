"""Tests for insight compiler."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

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

    ic.update_insights([log])
    manifest = json.loads(manifest_file.read_text())
    assert manifest["version"] == "0.1.2"
    assert manifest["updated"] != first_time


def test_connector_invoked(tmp_path, monkeypatch):
    insight_file = tmp_path / "insights.json"
    manifest_file = tmp_path / "manifest.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)
    monkeypatch.setattr(ic, "INSIGHT_MANIFEST_FILE", manifest_file)

    called: dict = {}

    def fake_post(url, json, timeout):  # noqa: A002 - match requests signature
        called["url"] = url
        called["json"] = json
        return object()

    monkeypatch.setenv("ARCHETYPE_SCORE_WEBHOOK_URL", "http://example.com")
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

