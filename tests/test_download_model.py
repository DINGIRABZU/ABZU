import sys
import importlib
from types import ModuleType
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_main_invokes_snapshot_download(monkeypatch):
    # Provide dummy dotenv module
    dummy_dotenv = ModuleType("dotenv")
    dummy_dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "dotenv", dummy_dotenv)

    # Capture calls to snapshot_download
    calls = {}
    def dummy_snapshot_download(**kwargs):
        calls.update(kwargs)
    dummy_hf = ModuleType("huggingface_hub")
    dummy_hf.snapshot_download = dummy_snapshot_download
    monkeypatch.setitem(sys.modules, "huggingface_hub", dummy_hf)

    # Import the module under test
    download_model = importlib.import_module("download_model")

    # Set token env variable
    monkeypatch.setenv("HF_TOKEN", "test-token")

    download_model.main()

    expected_dir = str(Path("INANNA_AI") / "models" / "DeepSeek-R1")
    assert calls == {
        "repo_id": "deepseek-ai/DeepSeek-R1",
        "token": "test-token",
        "local_dir": expected_dir,
        "local_dir_use_symlinks": False,
    }
