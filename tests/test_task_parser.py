"""Tests for task parser."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "task_parser", ROOT / "src" / "core" / "task_parser.py"
)
task_parser = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(task_parser)


def test_parse_detects_intents():
    text = "Please appear to me and initiate sacred communion."
    intents = task_parser.parse(text)
    assert {"intent": "appear", "action": "show_avatar"} in intents
    assert {"intent": "communion", "action": "start_call"} in intents


def test_parse_returns_empty_for_unknown():
    assert task_parser.parse("just a normal message") == []


def test_parse_case_insensitive():
    intents = task_parser.parse("APPEAR TO ME")
    assert intents == [{"intent": "appear", "action": "show_avatar"}]
