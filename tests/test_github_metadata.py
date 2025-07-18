import sys
import json
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.learning import github_metadata as gm


def test_fetch_repo_metadata(monkeypatch):
    class DummyResp:
        def raise_for_status(self):
            return None
        def json(self):
            return {"stargazers_count": 42, "updated_at": "2024-01-01"}
    dummy_req = types.ModuleType("requests")
    dummy_req.get = lambda *a, **k: DummyResp()
    monkeypatch.setattr(gm, "requests", dummy_req)
    monkeypatch.setattr(gm, "_headers", lambda: {})

    data = gm.fetch_repo_metadata("psf/requests")
    assert data == {"stars": 42, "updated": "2024-01-01"}


def test_build_and_save_metadata(monkeypatch, tmp_path):
    mapping = {"Alpha": ["https://github.com/psf/requests"]}
    monkeypatch.setattr(gm, "fetch_repo_metadata", lambda repo: {"stars": 1, "updated": repo})

    meta = gm.build_metadata(mapping)
    assert meta == {"Alpha": {"psf/requests": {"stars": 1, "updated": "psf/requests"}}}

    out = tmp_path / "repos.json"
    gm.save_metadata(meta, out)
    assert json.loads(out.read_text()) == meta
