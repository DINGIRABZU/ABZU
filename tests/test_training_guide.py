from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub out optional dependencies
sys.modules.setdefault("requests", types.ModuleType("requests"))
bs4_mod = types.ModuleType("bs4")
bs4_mod.BeautifulSoup = lambda *a, **k: None
sys.modules.setdefault("bs4", bs4_mod)

from INANNA_AI.learning import training_guide as tg


def test_parse_training_guide_dedup(tmp_path):
    guide = tmp_path / "guide.md"
    guide.write_text(
        """## Alpha
- https://github.com/user/repo#readme
- https://github.com/other/repo

## Beta
- https://github.com/user/repo
- https://github.com/new/repo/
""",
        encoding="utf-8",
    )
    mapping = tg.parse_training_guide(guide)
    assert mapping == {
        "Alpha": [
            "https://github.com/user/repo",
            "https://github.com/other/repo",
        ],
        "Beta": ["https://github.com/new/repo"],
    }


def test_write_repo_list(tmp_path):
    mapping = {
        "Alpha": ["https://github.com/user/repo", "https://github.com/other/repo"]
    }
    dest = tmp_path / "out.txt"
    tg.write_repo_list(mapping, dest)
    assert dest.read_text(encoding="utf-8").splitlines() == [
        "user/repo",
        "other/repo",
    ]
