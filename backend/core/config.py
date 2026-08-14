from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIRECTORY / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="DECISIONFORGE_",
    )

    DATABASE_URL: str
    ENVIRONMENT: Literal["development", "production"] = "development"
    API_PREFIX: str
    DEBUG: bool
    ALLOWED_ORIGINS: list[str]
    OPENAI_API_KEY: str
    GENERATION_API_KEY: str = "local-development-key"
    GENERATION_ENABLED: bool = True
    GENERATION_COOLDOWN_SECONDS: int = 15
    MAX_GENERATIONS_PER_SESSION_PER_DAY: int = 5
    MAX_GENERATIONS_PER_DAY: int = 20
    SESSION_SECRET_KEY: str = "local-session-secret-change-in-production"
    SESSION_MAX_AGE_SECONDS: int = 2_592_000
    COOKIE_SECURE: bool = False
    QUALIFICATION_TIMEOUT_SECONDS: int = 30
    GENERATION_REQUEST_TIMEOUT_SECONDS: int = 75
    GENERATION_JOB_TIMEOUT_SECONDS: int = 210

    @model_validator(mode="after")
    def resolve_relative_sqlite_path(self):
        relative_prefix = "sqlite:///./"

        if self.DATABASE_URL.startswith(relative_prefix):
            relative_path = self.DATABASE_URL.removeprefix(
                relative_prefix
            )
            absolute_path = (
                BACKEND_DIRECTORY / relative_path
            ).resolve()
            self.DATABASE_URL = f"sqlite:///{absolute_path}"

        if self.ENVIRONMENT == "production":
            unsafe_secrets = {
                "GENERATION_API_KEY": self.GENERATION_API_KEY,
                "SESSION_SECRET_KEY": self.SESSION_SECRET_KEY,
            }
            for name, value in unsafe_secrets.items():
                if len(value) < 32 or "change-in-production" in value:
                    raise ValueError(
                        f"{name} must be a random secret of at least "
                        "32 characters in production"
                    )

            if self.OPENAI_API_KEY == "your-openai-api-key":
                raise ValueError(
                    "OPENAI_API_KEY must be configured in production"
                )

            if self.DATABASE_URL.startswith("sqlite:"):
                raise ValueError(
                    "Production must use a persistent database, not SQLite"
                )

            if not self.COOKIE_SECURE:
                raise ValueError(
                    "COOKIE_SECURE must be enabled in production"
                )

        return self


settings = Settings()
