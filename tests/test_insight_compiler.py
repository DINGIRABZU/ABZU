import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import insight_compiler as ic  # noqa: E402


def test_update_aggregates(tmp_path, monkeypatch):
    insight_file = tmp_path / "insights.json"
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)

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
    monkeypatch.setattr(ic, "INSIGHT_FILE", insight_file)

    log = {
        "intent": "conjure fire",
        "tone": "joy",
        "emotion": "joy",
        "text": "ignite \U0001F702",
        "success": True,
    }

    ic.update_insights([log])
    data = json.loads(insight_file.read_text())
    assert data["conjure fire"]["resonance_index"]["joy"] == 1

    ic.update_insights([log])
    data = json.loads(insight_file.read_text())
    assert data["conjure fire"]["resonance_index"]["joy"] == 2
