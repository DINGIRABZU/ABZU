from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

from agents.nazarick.ethics_manifesto import LAWS

base = Path(__file__).resolve().parents[2] / "agents" / "razar"

mission_name = "agents.razar.mission_logger"
mission_spec = importlib.util.spec_from_file_location(mission_name, base / "mission_logger.py")
mission_logger = importlib.util.module_from_spec(mission_spec)
sys.modules[mission_name] = mission_logger
assert mission_spec and mission_spec.loader
mission_spec.loader.exec_module(mission_logger)

retro_bootstrap = types.ModuleType("retro_bootstrap")
def _dummy_bootstrap():
    return []
retro_bootstrap.bootstrap_from_docs = _dummy_bootstrap
sys.modules["agents.razar.retro_bootstrap"] = retro_bootstrap

stub = types.ModuleType("agents.razar")
stub.mission_logger = mission_logger
stub.retro_bootstrap = retro_bootstrap
sys.modules["agents.razar"] = stub

spec = importlib.util.spec_from_file_location(
    "agents.razar.cli", base / "cli.py"
)
cli = importlib.util.module_from_spec(spec)
sys.modules["agents.razar.cli"] = cli
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


def test_timeline_displays_boot_history(tmp_path, capsys):
    mission_logger.LOG_PATH = tmp_path / "logs" / "razar.log"
    mission_logger.log_start("alpha", "success")

    cli.main(["timeline"])
    out = capsys.readouterr().out.strip()
    assert "alpha" in out
    assert "start" in out


def test_bootstrap_invokes_retro_bootstrap(monkeypatch, capsys):
    called = []

    def fake_bootstrap_from_docs():
        called.append(True)
        return [Path("mod.py")]

    monkeypatch.setattr(cli.retro_bootstrap, "bootstrap_from_docs", fake_bootstrap_from_docs)
    cli.main(["bootstrap", "--from-docs"])
    out = capsys.readouterr().out.strip().splitlines()
    assert called
    assert out == ["mod.py"]
