import sys
import json
from pathlib import Path
import base64
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("requests", types.ModuleType("requests"))
bs4_mod = types.ModuleType("bs4")
bs4_mod.BeautifulSoup = lambda *a, **k: None
sys.modules.setdefault("bs4", bs4_mod)
numpy_mod = types.ModuleType("numpy")
numpy_mod.ndarray = object
sys.modules.setdefault("numpy", numpy_mod)

from INANNA_AI.learning import github_scraper as gs


def test_fetch_repo_writes_labels(monkeypatch, tmp_path):
    content = "alpha"
    encoded = base64.b64encode(content.encode()).decode()
    commits = [
        {
            "commit": {
                "message": "msg",
                "committer": {"date": "2024-01-01"},
            }
        }
    ]

    class DummyResp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self._data

    def dummy_get(url, headers=None, params=None, timeout=10):
        if url.endswith("/readme"):
            return DummyResp({"content": encoded})
        if url.endswith("/commits"):
            return DummyResp(commits)
        raise AssertionError("unexpected")

    monkeypatch.setattr(gs, "_headers", lambda: {})
    monkeypatch.setattr(gs, "requests", types.SimpleNamespace(get=dummy_get))
    monkeypatch.setattr(
        gs.github_metadata,
        "fetch_repo_metadata",
        lambda repo: {"stars": 1, "updated": "2024-01-01"},
    )

    labels = {
        "ritual_function": "github_scrape",
        "alchemical_math": 0.5,
        "emotion_tag": "joy",
        "intent_pattern": "alpha",
    }

    gs.fetch_repo("psf/requests", dest_dir=tmp_path, labels=labels)
    meta = json.loads((tmp_path / "psf_requests_metadata.json").read_text())

    for k, v in labels.items():
        assert meta[k] == v


def test_fetch_all_filters_using_insight(monkeypatch, tmp_path):
    repos = ["alpha/beta", "gamma/delta"]
    repo_file = tmp_path / "repos.txt"
    repo_file.write_text("\n".join(repos), encoding="utf-8")

    insight_file = tmp_path / "insight.json"
    insight_file.write_text(
        json.dumps({"beta": {"action_success_rate": 1.0, "best_tone": "calm"}}),
        encoding="utf-8",
    )

    saved = []

    def dummy_fetch_repo(repo, dest_dir=None, labels=None):
        saved.append(labels)
        return []

    monkeypatch.setattr(gs, "fetch_repo", dummy_fetch_repo)

    gs.fetch_all(repo_file, insight_file)

    assert saved == [
        {
            "ritual_function": "github_scrape",
            "alchemical_math": 1.0,
            "emotion_tag": "calm",
            "intent_pattern": "beta",
        }
    ]

