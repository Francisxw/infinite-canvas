from app.config import get_settings
from app.services.providers.base import ModelProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.openrouter_provider import OpenRouterProvider
from app.services.account_store import account_store


def get_provider(
    provider_name: str | None = None, *, user_id: str | None = None
) -> ModelProvider:
    settings = get_settings()
    resolved = (provider_name or settings.default_provider).lower().strip()

    if resolved == "openai":
        return OpenAIProvider()

    user_api_key = None
    if user_id:
        credentials, _ = account_store.get_openrouter_credentials(user_id)
        user_record = account_store.get_full_user(user_id)
        if user_record["openrouter_mode"] == "custom":
            user_api_key = credentials

    return OpenRouterProvider(api_key=user_api_key)
