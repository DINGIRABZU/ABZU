"""Application configuration loaded from environment variables."""
from __future__ import annotations

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Settings pulled from environment variables.

    The field names correspond to environment variables using Pydantic's
    standard mapping rules (``field_name" -> "FIELD_NAME").
    """

    glm_command_token: str | None = Field(None, env="GLM_COMMAND_TOKEN")
    crown_tts_backend: str = Field("gtts", env="CROWN_TTS_BACKEND")
    voice_avatar_config_path: str | None = Field(
        None, env="VOICE_AVATAR_CONFIG_PATH"
    )
    rvc_preset: str | None = Field(None, env="RVC_PRESET")
    voicefix: bool = Field(False, env="VOICEFIX")

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
