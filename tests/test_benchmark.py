import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI_AGENT import benchmark_preprocess


def test_benchmark_script_runs(tmp_path, monkeypatch, capsys):
    text_dir = tmp_path / "INANNA_AI"
    text_dir.mkdir()
    (text_dir / "sample.md").write_text("hello world", encoding="utf-8")

    config = tmp_path / "source_paths.json"
    config.write_text(json.dumps({"source_paths": [str(text_dir)]}), encoding="utf-8")

    monkeypatch.setattr(benchmark_preprocess.source_loader, "DEFAULT_CONFIG", config)
    monkeypatch.chdir(tmp_path)

    benchmark_preprocess.main()
    out = capsys.readouterr().out
    assert "Processed" in out
