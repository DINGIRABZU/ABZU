import sys
from pathlib import Path
import builtins

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util
from importlib.machinery import SourceFileLoader

spiral_os_path = ROOT / "spiral_os"
loader = SourceFileLoader("spiral_os", str(spiral_os_path))
spec = importlib.util.spec_from_loader("spiral_os", loader)
spiral_os = importlib.util.module_from_spec(spec)
loader.exec_module(spiral_os)


def test_deploy_pipeline_runs_commands(monkeypatch, tmp_path):
    # create simple pipeline YAML
    yaml_text = """
steps:
  - name: greet
    run: echo hello
"""
    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(yaml_text)

    calls = []

    def fake_run(args, check):
        calls.append(args)
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    spiral_os.deploy_pipeline(str(pipeline))

    assert calls == [["echo", "hello"]]


def test_deploy_pipeline_multiline(monkeypatch, tmp_path):
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

    def fake_run(args, check):
        calls.append(args)
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    spiral_os.deploy_pipeline(str(pipeline))

    assert calls == [["echo", "hello", "world"]]
