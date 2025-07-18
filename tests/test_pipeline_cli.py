from __future__ import annotations
import sys
from pathlib import Path
import importlib.util
from importlib.machinery import SourceFileLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spiral_os_path = ROOT / "spiral_os"
loader = SourceFileLoader("spiral_os", str(spiral_os_path))
spec = importlib.util.spec_from_loader("spiral_os", loader)
spiral_os = importlib.util.module_from_spec(spec)
loader.exec_module(spiral_os)


def test_cli_executes_steps_in_order(monkeypatch, tmp_path):
    yaml_text = """
steps:
  - name: first
    run: echo one
  - name: second
    run: echo two
"""
    pipeline = tmp_path / "pipeline.yaml"
    pipeline.write_text(yaml_text)

    calls: list[list[str]] = []

    def fake_run(args, check=True):
        calls.append(args)
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(spiral_os.subprocess, "run", fake_run)

    spiral_os.main(["pipeline", "deploy", str(pipeline)])

    assert calls == [["echo", "one"], ["echo", "two"]]
