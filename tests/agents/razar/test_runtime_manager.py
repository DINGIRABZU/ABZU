import json
import logging


def test_runtime_manager_resume(failing_runtime, caplog):
    manager, fix_beta, tmp_path, quarantine_dir = failing_runtime

    # First run – beta fails and is quarantined
    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert not success
    assert (tmp_path / "alpha.txt").exists()
    assert not (tmp_path / "beta.txt").exists()
    assert not (tmp_path / "gamma.txt").exists()
    state = json.loads((tmp_path / "run.state").read_text(encoding="utf-8"))
    assert state["last_component"] == "alpha"
    assert (quarantine_dir / "beta.json").exists()

    # Second run – fix beta command and ensure resume
    fix_beta()
    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert success
    assert (tmp_path / "beta.txt").exists()
    assert (tmp_path / "gamma.txt").exists()
    state = json.loads((tmp_path / "run.state").read_text(encoding="utf-8"))
    assert state["last_component"] == "gamma"
    assert any("Starting component beta" in r.message for r in caplog.records)
