import json

from agents.razar.state_validator import DEFAULT_STATE, validate_state


def test_validate_state_with_valid_file(tmp_path):
    path = tmp_path / "razar_state.json"
    path.write_text(json.dumps(DEFAULT_STATE), encoding="utf-8")

    validate_state(path)

    assert not path.with_suffix(".json.bak").exists()
    assert json.loads(path.read_text(encoding="utf-8")) == DEFAULT_STATE


def test_validate_state_creates_missing_file(tmp_path):
    path = tmp_path / "missing_state.json"
    validate_state(path)
    assert json.loads(path.read_text(encoding="utf-8")) == DEFAULT_STATE
    assert not path.with_suffix(".json.bak").exists()


def test_validate_state_recreates_corrupt_file(tmp_path):
    path = tmp_path / "corrupt.json"
    corrupt = DEFAULT_STATE.copy()
    corrupt.pop("glm4v_present")  # violate schema
    path.write_text(json.dumps(corrupt), encoding="utf-8")

    validate_state(path)

    backup = path.with_suffix(".json.bak")
    assert backup.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == DEFAULT_STATE
