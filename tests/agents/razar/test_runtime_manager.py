import json
import logging

from agents.razar import quarantine_manager as qm


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
    assert state["history"] == ["alpha"]
    assert (quarantine_dir / "beta.json").exists()

    # Second run – fix beta command, reactivate and ensure resume
    fix_beta()
    qm.reactivate_component("beta", verified=True)
    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert success
    assert (tmp_path / "beta.txt").exists()
    assert (tmp_path / "gamma.txt").exists()
    state = json.loads((tmp_path / "run.state").read_text(encoding="utf-8"))
    assert state["last_component"] == "gamma"
    assert state["history"] == ["alpha", "beta", "gamma"]
    assert any("Starting component beta" in r.message for r in caplog.records)


def test_runtime_manager_skips_quarantined(failing_runtime, caplog):
    manager, fix_beta, tmp_path, quarantine_dir = failing_runtime

    # First run – beta fails and is quarantined
    manager.run()

    # Second run without reactivation should skip beta
    fix_beta()
    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert success
    assert not (tmp_path / "beta.txt").exists()
    assert (tmp_path / "gamma.txt").exists()
    state = json.loads((tmp_path / "run.state").read_text(encoding="utf-8"))
    assert state["last_component"] == "gamma"
    assert state["history"] == ["alpha", "gamma"]
    assert any(
        "Skipping quarantined component beta" in r.message for r in caplog.records
    )
