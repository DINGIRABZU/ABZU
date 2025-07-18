from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub optional dependencies
sys.modules.setdefault("requests", types.ModuleType("requests"))
bs4_mod = types.ModuleType("bs4")
bs4_mod.BeautifulSoup = lambda *a, **k: None
sys.modules.setdefault("bs4", bs4_mod)

from INANNA_AI.learning import training_guide as tg
from INANNA_AI.learning import github_metadata as gm

SAMPLE_GUIDE = """## 𒀭 ME – NAMMU
- https://github.com/HuangOwen/Awesome-LLM-Compression
- https://github.com/51j0/Android-Storage-Extractor

## 𒀭 ME – TÂMTU
- https://github.com/libAudioFlux/audioFlux
- https://github.com/willianjusten/awesome-audio-visualization
- https://github.com/willianjusten/awesome-audio-visualization#readme
- https://github.com/willianjusten/awesome-audio-visualization
- https://github.com/faroit/awesome-python-scientific-audio
- https://github.com/faroit/awesome-python-scientific-audio#readme

## 𒀭 ME – ERESH’NAM
- https://github.com/ashishb/android-security-awesome#readme
- https://github.com/ashishb/android-security-awesome
"""

EXPECTED_MAPPING = {
    "𒀭 ME – NAMMU": [
        "https://github.com/HuangOwen/Awesome-LLM-Compression",
        "https://github.com/51j0/Android-Storage-Extractor",
    ],
    "𒀭 ME – TÂMTU": [
        "https://github.com/libAudioFlux/audioFlux",
        "https://github.com/willianjusten/awesome-audio-visualization",
        "https://github.com/faroit/awesome-python-scientific-audio",
    ],
    "𒀭 ME – ERESH’NAM": [
        "https://github.com/ashishb/android-security-awesome",
    ],
}

def test_parse_training_guide_sample(tmp_path):
    guide = tmp_path / "guide.md"
    guide.write_text(SAMPLE_GUIDE, encoding="utf-8")
    mapping = tg.parse_training_guide(guide)
    assert mapping == EXPECTED_MAPPING

def test_write_repo_list_dedupe(tmp_path):
    guide = tmp_path / "guide.md"
    guide.write_text(SAMPLE_GUIDE, encoding="utf-8")
    mapping = tg.parse_training_guide(guide)
    dest = tmp_path / "repos.txt"
    tg.write_repo_list(mapping, dest)
    assert dest.read_text(encoding="utf-8").splitlines() == [
        "HuangOwen/Awesome-LLM-Compression",
        "51j0/Android-Storage-Extractor",
        "libAudioFlux/audioFlux",
        "willianjusten/awesome-audio-visualization",
        "faroit/awesome-python-scientific-audio",
        "ashishb/android-security-awesome",
    ]

def test_build_metadata_offline(tmp_path, monkeypatch):
    guide = tmp_path / "guide.md"
    guide.write_text(SAMPLE_GUIDE, encoding="utf-8")
    mapping = tg.parse_training_guide(guide)
    monkeypatch.setattr(gm, "fetch_repo_metadata", lambda repo: {"stars": 1, "updated": repo})
    meta = gm.build_metadata(mapping)
    assert meta["𒀭 ME – NAMMU"]["HuangOwen/Awesome-LLM-Compression"] == {"stars": 1, "updated": "HuangOwen/Awesome-LLM-Compression"}

