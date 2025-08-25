"""Tests for start dev agents triage."""

from __future__ import annotations

import json
import sys

import start_dev_agents
from corpus_memory_logging import log_interaction


def test_triage_writes_transcript(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    triage_dir = tmp_path / "data" / "triage_sessions"

    # redirect interactions file
    monkeypatch.setattr(
        start_dev_agents,
        "run_dev_cycle",
        lambda *a, **k: log_interaction("p", {}, {}, "ok"),
    )
    monkeypatch.setattr(start_dev_agents, "check_required", lambda _: None)
    monkeypatch.setattr(start_dev_agents, "load_env", lambda _p: None)

    monkeypatch.setattr(
        start_dev_agents.subprocess,
        "run",
        lambda *a, **k: type(
            "P", (), {"returncode": 1, "stdout": "fail", "stderr": ""}
        )(),
    )

    monkeypatch.setenv("PLANNER_MODEL", "p")
    monkeypatch.setenv("CODER_MODEL", "c")
    monkeypatch.setenv("REVIEWER_MODEL", "r")

    monkeypatch.setattr(
        "corpus_memory_logging.INTERACTIONS_FILE",
        tmp_path / "data" / "interactions.jsonl",
        raising=False,
    )

    argv = ["prog", "--triage", "tests/sample.py"]
    monkeypatch.setattr(sys, "argv", argv)
    start_dev_agents.main()

    files = list(triage_dir.glob("*.jsonl"))
    assert len(files) == 1
    content = files[0].read_text().strip()
    assert content
    for line in content.splitlines():
        record = json.loads(line)
        assert record["outcome"] == "ok"
