"""Tests for spiral os."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util
from importlib.machinery import SourceFileLoader

spiral_os_path = ROOT / "spiral_os"
loader = SourceFileLoader("spiral_os", str(spiral_os_path))
spec = importlib.util.spec_from_loader("spiral_os", loader)
spiral_os = importlib.util.module_from_spec(spec)
loader.exec_module(spiral_os)


@pytest.mark.parametrize("as_str", [True, False])
def test_deploy_pipeline_runs_commands(monkeypatch, tmp_path, as_str):
    # create simple pipeline YAML
    yaml_text = """
steps:
  - name: greet
    run: echo hello
"""
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml_text)

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    path_arg = str(pipeline) if as_str else pipeline
    spiral_os.deploy_pipeline(path_arg)

    cmd, kwargs = calls[0]
    assert cmd.strip().split() == ["echo", "hello"]
    assert kwargs["shell"] is True and kwargs["check"] is True


@pytest.mark.parametrize("as_str", [True, False])
def test_deploy_pipeline_multiline(monkeypatch, tmp_path, as_str):
    yaml_text = """
steps:
  - name: multi
    run: |
      echo hello \
        world
"""
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml_text)

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    path_arg = str(pipeline) if as_str else pipeline
    spiral_os.deploy_pipeline(path_arg)

    cmd, kwargs = calls[0]
    assert cmd.strip().split() == ["echo", "hello", "world"]
    assert kwargs["shell"] is True and kwargs["check"] is True


def test_deploy_pipeline_invalid_yaml(tmp_path, caplog):
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(":: not yaml ::")

    with caplog.at_level("ERROR"):
        with pytest.raises(yaml.YAMLError):
            spiral_os.deploy_pipeline(pipeline)

    assert "Failed to parse pipeline YAML" in caplog.text


def test_deploy_pipeline_command_failure(monkeypatch, tmp_path, caplog):
    yaml_text = """
steps:
  - run: ok
  - run: bad
"""
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml_text)

    def fake_run(cmd, **kwargs):
        if cmd.strip() == "bad":
            raise subprocess.CalledProcessError(1, cmd)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    with caplog.at_level("ERROR"):
        with pytest.raises(subprocess.CalledProcessError):
            spiral_os.deploy_pipeline(pipeline)

    assert "Command failed" in caplog.text
