from functools import lru_cache
import hashlib
import json
from base64 import urlsafe_b64encode
from typing import Annotated

from pydantic import field_validator, model_validator
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
    account_data_file: str = ".data/account_store.db"
    signup_bonus_points: int = 120
    account_session_ttl_hours: int = 720
    account_secret: str = ""
    wechat_pay_mchid: str = ""
    wechat_pay_appid: str = ""
    wechat_pay_private_key: str = ""
    wechat_pay_cert_serial_no: str = ""
    wechat_pay_apiv3_key: str = ""
    wechat_pay_notify_url: str = ""
    wechat_pay_cert_dir: str = ".data/wechatpay-cert"

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

    @field_validator("wechat_pay_notify_url")
    @classmethod
    def validate_notify_url(cls, v):
        if v and not v.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("WECHAT_PAY_NOTIFY_URL must be HTTPS in production")
        return v

    @model_validator(mode="after")
    def validate_production_config(self):
        if self.app_env == "production":
            if not self.account_secret:
                raise ValueError("account_secret must be set in production")
            if self.wechat_pay_notify_url and not self.wechat_pay_notify_url.startswith(
                "https://"
            ):
                raise ValueError("WECHAT_PAY_NOTIFY_URL must use HTTPS in production")
        elif self.app_env == "development" and not self.account_secret:
            # Only for development: use a default but warn via logs
            self.account_secret = "dev-local-account-secret-change-in-production"
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def derive_account_secret_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return urlsafe_b64encode(digest)
