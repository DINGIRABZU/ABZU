import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI_AGENT import source_loader


def test_load_config_relative_to_config(tmp_path, monkeypatch):
    config_dir = tmp_path / "cfg"
    text_dir = config_dir / "texts"
    text_dir.mkdir(parents=True)
    (text_dir / "a.md").write_text("hello", encoding="utf-8")

    config = config_dir / "source_paths.json"
    config.write_text(json.dumps({"source_paths": ["texts"]}), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    paths = source_loader.load_config(config)
    assert paths == [text_dir]

    texts = source_loader.load_sources(config)
    assert texts == {"a.md": "hello"}

    files = source_loader.list_markdown_files(config)
    assert files == [str(text_dir / "a.md")]
