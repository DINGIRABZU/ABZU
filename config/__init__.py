from __future__ import annotations

"""Application configuration loaded from environment variables."""
from pathlib import Path

from pydantic import AnyHttpUrl, Field

try:  # pragma: no cover - optional dependency
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback when dependency missing
    import os

    class BaseSettings:  # type: ignore[override]
        """Lightweight substitute when ``pydantic-settings`` is unavailable.

        This fallback mirrors the interface of ``BaseSettings`` used in the
        project just enough for tests.  Values are pulled from environment
        variables using the field names as keys, falling back to defaults when
        unset.
        """

        def dict(self):  # pragma: no cover - simple helper for tests
            return self.__dict__

        def __init__(self, **data):
            for name, default in self.__class__.__dict__.items():
                if name.startswith("_") or callable(default):
                    continue
                env_name = (
                    getattr(default, "json_schema_extra", {}).get("env")
                    if hasattr(default, "json_schema_extra")
                    else None
                )
                default_val = getattr(default, "default", default)
                raw = os.getenv(env_name or name.upper())
                if raw is None:
                    value = default_val
                else:
                    if isinstance(default_val, bool):
                        value = raw.lower() in {"1", "true", "yes"}
                    elif isinstance(default_val, int):
                        value = int(raw)
                    elif isinstance(default_val, float):
                        value = float(raw)
                    elif isinstance(default_val, Path):
                        value = Path(raw)
                    else:
                        value = raw
                setattr(self, name, value)

# ``config`` is now a package; resolve paths relative to the repository root.
BASE_DIR = Path(__file__).resolve().parent.parent


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
        BASE_DIR / "data" / "vector_memory",
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
