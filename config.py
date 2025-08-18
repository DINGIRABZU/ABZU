from __future__ import annotations

"""Application configuration loaded from environment variables."""
from pathlib import Path

from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    """Settings pulled from environment variables.

    The field names correspond to environment variables using Pydantic's
    standard mapping rules (``field_name" -> "FIELD_NAME").
    """

    glm_command_token: str | None = Field(None, env="GLM_COMMAND_TOKEN")
    crown_tts_backend: str = Field("gtts", env="CROWN_TTS_BACKEND")
    voice_avatar_config_path: Path | None = Field(
        None, env="VOICE_AVATAR_CONFIG_PATH"
    )
    rvc_preset: str | None = Field(None, env="RVC_PRESET")
    voicefix: bool = Field(False, env="VOICEFIX")
    glm_shell_url: AnyHttpUrl | None = Field(None, env="GLM_SHELL_URL")
    glm_shell_key: str | None = Field(None, env="GLM_SHELL_KEY")
    animation_service_url: AnyHttpUrl | None = Field(
        None, env="ANIMATION_SERVICE_URL"
    )
    embed_model_path: str = Field("all-MiniLM-L6-v2", env="EMBED_MODEL_PATH")
    retrain_threshold: int = Field(10, env="RETRAIN_THRESHOLD")
    llm_rotation_period: int = Field(300, env="LLM_ROTATION_PERIOD")
    llm_max_failures: int = Field(3, env="LLM_MAX_FAILURES")
    feedback_novelty_threshold: float = Field(
        0.3, env="FEEDBACK_NOVELTY_THRESHOLD"
    )
    feedback_coherence_threshold: float = Field(
        0.7, env="FEEDBACK_COHERENCE_THRESHOLD"
    )
    vector_db_path: Path = Field(
        Path(__file__).resolve().parent / "data" / "vector_memory",
        env="VECTOR_DB_PATH",
    )
    neo4j_uri: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field("neo4j", env="NEO4J_USER")
    neo4j_password: str = Field("password", env="NEO4J_PASSWORD")

    class Config:
        case_sensitive = True


settings = Settings()


def require(*names: str) -> None:
    """Ensure that the given configuration values are present.

    Parameters
    ----------
    names:
        Attribute names on :data:`settings` that must be truthy.

    Raises
    ------
    RuntimeError
        If any requested variables are unset.
    """

    missing = [name for name in names if getattr(settings, name) in (None, "")]
    if missing:
        plural = "s" if len(missing) > 1 else ""
        env_names = ", ".join(n.upper() for n in missing)
        raise RuntimeError(f"Missing required environment variable{plural}: {env_names}")


def reload() -> None:
    """Reload configuration from the current environment.

    Useful for tests that modify ``os.environ``.
    """
    global settings
    settings = Settings()
