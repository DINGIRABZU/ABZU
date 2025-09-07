from __future__ import annotations

import json

import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "message_formatter",
    Path(__file__).resolve().parents[2] / "connectors" / "message_formatter.py",
)
message_formatter = importlib.util.module_from_spec(spec)
assert spec.loader is not None  # for type checkers
spec.loader.exec_module(message_formatter)
format_message = message_formatter.format_message


def test_format_message_includes_metadata() -> None:
    msg = format_message("crown", "hello", version="1.2", recovery_url="url")
    data = json.loads(msg)
    assert data["content"] == "hello"
    assert data["chakra"] == "crown"
    assert data["version"] == "1.2"
    assert data["recovery_url"] == "url"


def test_format_message_defaults_present() -> None:
    msg = format_message("root", "hi")
    data = json.loads(msg)
    assert data["content"] == "hi"
    assert data["chakra"] == "root"
    assert data["version"]
    assert data["recovery_url"]
