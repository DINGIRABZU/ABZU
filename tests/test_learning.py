import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types
sys.modules.setdefault("requests", types.ModuleType("requests"))
bs4_mod = types.ModuleType("bs4")
bs4_mod.BeautifulSoup = lambda *a, **k: None
sys.modules.setdefault("bs4", bs4_mod)

from INANNA_AI.learning import project_gutenberg as pg
from INANNA_AI.learning import github_scraper as gs


def test_chunk_splits_text():
    text = "one two three four five"
    chunks = pg.chunk(text, 2)
    assert chunks == ["one two", "three four", "five"]


def test_load_repo_list(tmp_path):
    file = tmp_path / "repos.txt"
    file.write_text("psf/requests\n# comment\nnumpy/numpy", encoding="utf-8")
    repos = gs.load_repo_list(file)
    assert repos == ["psf/requests", "numpy/numpy"]
