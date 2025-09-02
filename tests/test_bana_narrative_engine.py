"""Tests for Bana narrative engine multitrack composition."""

from pathlib import Path
import csv

from memory.narrative_engine import StoryEvent, compose_multitrack_story


def test_multitrack_tracks_present():
    """Biosignal events yield full multitrack story output."""
    csv_path = Path("data/biosignals/sample_biosignals.csv")
    events = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            action = "elevated heart rate" if float(row["heart_rate"]) > 74 else "calm"
            events.append(StoryEvent(actor="subject", action=action))
    result = compose_multitrack_story(events)
    assert set(result) == {"prose", "audio", "visual", "usd"}
    assert result["prose"]
    for track in ("audio", "visual", "usd"):
        assert isinstance(result[track], list) and result[track]
