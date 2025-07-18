import sys
from pathlib import Path
import types
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
dummy_np = types.ModuleType("numpy")
dummy_np.clip = lambda a, mn, mx: a
sys.modules.setdefault("numpy", dummy_np)

from INANNA_AI import utils


def test_verify_insight_matrix_raises_on_missing():
    matrix = {
        "spell": {"counts": {"emotions": {"joy": {"total": 1}}}}
    }
    with pytest.raises(KeyError):
        utils.verify_insight_matrix(matrix, emotion_keys=["joy", "sad"])
