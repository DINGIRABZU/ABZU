import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import db_storage


def test_log_and_fetch_feedback(tmp_path):
    db = tmp_path / "f.db"
    db_storage.init_db(db)
    db_storage.log_feedback("calm", 0.8, 0.9, 0.7, db_path=db)
    db_storage.log_feedback("joy", 1.0, 1.0, 1.0, db_path=db)

    all_rows = db_storage.fetch_feedback(db_path=db)
    assert len(all_rows) == 2
    assert all_rows[0]["emotion"] == "joy"
    assert all_rows[1]["satisfaction"] == 0.8

    limited = db_storage.fetch_feedback(limit=1, db_path=db)
    assert len(limited) == 1
    assert limited[0]["emotion"] == "joy"

