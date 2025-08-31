from __future__ import annotations

from pathlib import Path

import pytest

from memory import narrative_engine
from scripts.ingest_biosignals import ingest_file
from src.core.model_selector import ModelSelector
import servant_model_manager

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "biosignals"

__version__ = "0.1.0"


def test_ingestion_to_mistral_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pipeline from CSV ingestion to mocked Mistral output."""
    csv_path = DATA_DIR / "sample_biosignals_beta.csv"
    logged: list[str] = []
    monkeypatch.setattr(narrative_engine, "log_story", lambda text: logged.append(text))
    monkeypatch.setattr(
        "scripts.ingest_biosignals.log_story", lambda text: logged.append(text)
    )
    ingest_file(csv_path)
    assert logged and all(entry == "elevated heart rate" for entry in logged)

    event = narrative_engine.StoryEvent(actor="subject", action=logged[0])
    selector = ModelSelector()
    model = selector.select_model(
        task="narrative", emotion="stress", weight=1.0, history=[]
    )
    assert model == "mistral"

    servant_model_manager.register_model("mistral", lambda prompt: f"mistral:{prompt}")
    output = servant_model_manager.invoke_sync(
        "mistral", f"{event.actor}:{event.action}"
    )
    assert output == "mistral:subject:elevated heart rate"


def test_stream_stories(monkeypatch: pytest.MonkeyPatch) -> None:
    """`stream_stories` yields events in insertion order."""
    monkeypatch.setattr(narrative_engine, "_STORY_LOG", [])
    narrative_engine.log_story("alpha")
    narrative_engine.log_story("beta")
    assert list(narrative_engine.stream_stories()) == ["alpha", "beta"]
