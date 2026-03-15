from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Infinite Canvas Backend"
    app_env: str = "development"
    default_provider: str = "openrouter"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    allowed_origins: str = "http://localhost:5173"
    upload_max_mb: int = 20


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
