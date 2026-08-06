from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str
    API_PREFIX: str
    DEBUG: bool
    ALLOWED_ORIGINS: list[str]
    OPENAI_API_KEY: str


settings = Settings()
