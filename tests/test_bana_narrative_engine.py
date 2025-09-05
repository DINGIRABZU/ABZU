"""Tests for Bana narrative engine multitrack composition."""

from pathlib import Path
import csv
import json

from memory.narrative_engine import StoryEvent, compose_multitrack_story


def test_multitrack_track_schemas() -> None:
    """Biosignal events yield full multitrack story output with valid schemas."""
    csv_path = Path("data/biosignals/sample_biosignals.csv")
    events = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            action = "elevated heart rate" if float(row["heart_rate"]) > 74 else "calm"
            events.append(StoryEvent(actor="subject", action=action))
    result = compose_multitrack_story(events)

    assert set(result) == {"prose", "audio", "visual", "usd"}
    assert isinstance(result["prose"], str) and result["prose"]

    assert isinstance(result["audio"], list) and result["audio"]
    assert all(
        isinstance(a, dict) and set(a) == {"cue"} and isinstance(a["cue"], str)
        for a in result["audio"]
    )

    assert isinstance(result["visual"], list) and result["visual"]
    assert all(
        isinstance(v, dict)
        and set(v) == {"directive"}
        and isinstance(v["directive"], str)
        for v in result["visual"]
    )

    assert isinstance(result["usd"], list) and result["usd"]
    assert all(
        isinstance(u, dict)
        and set(u) == {"op", "path", "action"}
        and all(isinstance(u[k], str) for k in ("op", "path", "action"))
        for u in result["usd"]
    )


def test_multitrack_story_golden_file() -> None:
    """`compose_multitrack_story` output matches the recorded sample."""
    events = [
        StoryEvent(actor="hero", action="smiles"),
        StoryEvent(actor="villain", action="frowns"),
    ]
    result = compose_multitrack_story(events)
    data_dir = Path("tests/data/bana")
    for track in ("prose", "audio", "visual", "usd"):
        with (data_dir / f"{track}.json").open(encoding="utf-8") as f:
            expected = json.load(f)
        assert result[track] == expected, f"{track} track mismatch"
