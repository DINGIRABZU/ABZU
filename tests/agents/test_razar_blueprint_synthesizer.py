"""Tests for razar blueprint synthesizer."""

from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "razar_blueprint_synthesizer",
    Path(__file__).resolve().parents[2]
    / "agents"
    / "razar"
    / "blueprint_synthesizer.py",
)
blueprint = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(blueprint)
synthesize = blueprint.synthesize


def test_synthesize_includes_manifesto(tmp_path):
    output = tmp_path / "graph.json"
    graph = synthesize(output)
    root = Path(__file__).resolve().parents[2]
    manifesto = (root / "docs" / "nazarick_manifesto.md").resolve()
    assert str(manifesto) in graph.nodes
    assert output.exists()
