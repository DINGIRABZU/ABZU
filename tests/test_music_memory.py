from pathlib import Path

import numpy as np

from memory.music_memory import add_track, query_tracks


def test_add_and_query(tmp_path: Path) -> None:
    db = tmp_path / "music.db"
    emb1 = np.array([1.0, 0.0, 0.0], dtype=float)
    emb2 = np.array([0.0, 1.0, 0.0], dtype=float)
    add_track(emb1, {"name": "a"}, "happy", db_path=db)
    add_track(emb2, {"name": "b"}, "sad", db_path=db)

    res = query_tracks(np.array([1.0, 0.0, 0.0], dtype=float), db_path=db)
    assert res[0]["metadata"]["name"] == "a"

    res_emotion = query_tracks(
        np.array([0.0, 1.0, 0.0], dtype=float), emotion="sad", db_path=db
    )
    assert res_emotion[0]["emotion"] == "sad"
