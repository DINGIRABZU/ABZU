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


def test_fetch_repo_fetches_and_embeds(monkeypatch, tmp_path):
    content = "hello"
    encoded = base64.b64encode(content.encode()).decode()
    commits = [
        {
            "commit": {
                "message": "First",
                "committer": {"date": "2024-01-02"},
            }
        },
        {
            "commit": {
                "message": "Second",
                "committer": {"date": "2024-01-01"},
            }
        },
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
        raise AssertionError("unexpected url")

    monkeypatch.setattr(gs, "_headers", lambda: {})
    monkeypatch.setattr(gs, "requests", types.SimpleNamespace(get=dummy_get))
    monkeypatch.setattr(gs.github_metadata, "fetch_repo_metadata", lambda repo: {"stars": 5, "updated": "2023-12-30"})

    added = {}

    def dummy_add(col, texts, model):
        added.update(texts)

    monkeypatch.setattr(gs.corpus_memory, "add_embeddings", dummy_add)
    monkeypatch.setattr(gs.corpus_memory, "create_collection", lambda: "COL")
    monkeypatch.setattr(gs, "SentenceTransformer", lambda name: types.SimpleNamespace(encode=lambda t, convert_to_numpy=True: [[0.1]] * len(t)))

    paths = gs.fetch_repo("psf/requests", dest_dir=tmp_path)

    readme_path = tmp_path / "psf_requests_README.md"
    commits_path = tmp_path / "psf_requests_COMMITS.txt"
    meta_path = tmp_path / "psf_requests_metadata.json"

    assert set(paths) == {readme_path, commits_path, meta_path}
    assert readme_path.read_text() == content
    assert "First" in commits_path.read_text()
    meta = json.loads(meta_path.read_text())
    assert meta["stars"] == 5
    assert meta["last_commit"] == "2024-01-02"
    assert str(readme_path) in added
    assert str(commits_path) in added


def test_fetch_all_uses_repo_list(monkeypatch, tmp_path):
    repos = ["a/b", "c/d"]
    monkeypatch.setattr(gs, "load_repo_list", lambda p=None: repos)

    saved = []
    def dummy_fetch_repo(repo, dest_dir=None, labels=None):
        paths = []
        for suffix in ["README.md", "COMMITS.txt", "metadata.json"]:
            p = tmp_path / f"{repo.replace('/', '_')}_{suffix}"
            p.write_text(repo, encoding="utf-8")
            paths.append(p)
        saved.append(repo)
        return paths

    monkeypatch.setattr(gs, "fetch_repo", dummy_fetch_repo)

    files = gs.fetch_all(Path("dummy"))
    assert saved == repos
    assert len(files) == 6
