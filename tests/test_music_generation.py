import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import music_generation as mg


def test_generate_from_text_creates_file(tmp_path, monkeypatch):
    calls = {}

    def fake_pipeline(task, model):
        calls['task'] = task
        calls['model'] = model

        class P:
            def __call__(self, prompt):
                calls['prompt'] = prompt
                return [{"audio": b"WAV"}]

        return P()

    monkeypatch.setattr(mg, "hf_pipeline", fake_pipeline)
    monkeypatch.setattr(mg, "OUTPUT_DIR", tmp_path)

    out = mg.generate_from_text("beat", model="musicgen")

    assert out.exists()
    assert out.parent == tmp_path
    assert calls == {
        'task': 'text-to-audio',
        'model': mg.MODEL_IDS['musicgen'],
        'prompt': 'beat',
    }

