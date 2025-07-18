import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rag_parser


def test_load_inputs_chunking(tmp_path):
    base = tmp_path
    # Root file
    (base / "test.txt").write_text("hello", encoding="utf-8")
    # JSON
    (base / "data.json").write_text('{"a": 1}', encoding="utf-8")
    # Notebook
    (base / "nb.ipynb").write_text("{}", encoding="utf-8")
    # Archetype folder
    arch = base / "alpha"
    arch.mkdir()
    (arch / "doc.md").write_text("content", encoding="utf-8")
    long_text = "x" * 2100
    (arch / "code.py").write_text(long_text, encoding="utf-8")

    res = rag_parser.load_inputs(base)
    assert len(res) == 6

    code_chunks = [c for c in res if Path(c["source_path"]).name == "code.py"]
    assert len(code_chunks) == 2
    assert len(code_chunks[0]["text"]) == 2000
    assert len(code_chunks[1]["text"]) == 100

    alpha_items = [c for c in res if c.get("archetype") == "alpha"]
    assert alpha_items
