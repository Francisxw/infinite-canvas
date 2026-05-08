import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Infinite Studio Backend"
    app_env: str = "development"
    default_provider: str = "openrouter"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_referer: str = "http://localhost:15191"
    openrouter_title: str = "Infinite Studio"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    allowed_origins: Annotated[
        list[str],
        NoDecode,
    ] = ["http://localhost:15191", "http://127.0.0.1:15191"]
    upload_max_mb: int = 20

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


def get_settings() -> Settings:
    return Settings()
