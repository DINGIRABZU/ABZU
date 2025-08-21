from pathlib import Path

import crown_config


def test_env_aliases(monkeypatch):
    monkeypatch.setenv("GLM_COMMAND_TOKEN", "tok")
    monkeypatch.setenv("VECTOR_DB_PATH", str(Path("/tmp/vector")))
    crown_config.reload()
    assert crown_config.settings.glm_command_token == "tok"
    assert crown_config.settings.vector_db_path == Path("/tmp/vector")
