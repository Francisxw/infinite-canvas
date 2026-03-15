from app.config import get_settings
from app.services.providers.base import ModelProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.openrouter_provider import OpenRouterProvider


def get_provider(provider_name: str | None = None) -> ModelProvider:
    settings = get_settings()
    resolved = (provider_name or settings.default_provider).lower().strip()

    if resolved == "openai":
        return OpenAIProvider()

    return OpenRouterProvider()
