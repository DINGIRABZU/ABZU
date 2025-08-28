from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from agents.nazarick.ethics_manifesto import LAWS

spec = importlib.util.spec_from_file_location(
    "razar_cli", Path(__file__).resolve().parents[2] / "agents" / "razar" / "cli.py"
)
cli = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cli)


def test_ethics_lists_manifesto_laws(capsys):
    cli.main(["ethics"])
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == len(LAWS)
    assert out[0].startswith("1. " + LAWS[0].name)


def test_trust_outputs_score_and_protocol(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["trust", "shalltear"])
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert "Trust: 5" in out_lines[0]
    assert out_lines[1].startswith("Protocol: nazarick_rank1_")
