from collections.abc import Iterator
from typing import Any

from app.config import get_settings
from app.services.providers.base import (
    ModelProvider,
    ProviderConfigurationError,
    provider_get_json,
    provider_post_json,
)


def _traverse_provider_response(
    data: dict[str, Any],
    *,
    url_keys: set[str],
    container_keys: set[str],
    max_depth: int = 6,
) -> Iterator[str]:
    """Recursively extract URLs from provider responses.

    Args:
        data: The response payload to traverse
        url_keys: Keys that may contain URL values (directly or in nested dict)
        container_keys: Keys containing arrays of items to traverse
        max_depth: Maximum recursion depth to prevent infinite loops

    Yields:
        Unique URL strings found in the response
    """
    seen: set[str] = set()

    def extract(value: Any, depth: int) -> Iterator[str]:
        if depth > max_depth or value is None:
            return

        if isinstance(value, str):
            if value and value not in seen:
                seen.add(value)
                yield value
            return

        if isinstance(value, list):
            for item in value:
                yield from extract(item, depth + 1)
            return

        if not isinstance(value, dict):
            return

        for key, val in value.items():
            if key in url_keys:
                if isinstance(val, str):
                    yield from extract(val, depth)
                elif isinstance(val, dict):
                    yield from extract(val.get("url"), depth)
            elif key in container_keys:
                if isinstance(val, list):
                    for item in val:
                        yield from extract(item, depth + 1)
            elif key in {"content", "message"}:
                yield from extract(val, depth + 1)
            else:
                yield from extract(val, depth + 1)

    yield from extract(data, 0)


class OpenRouterProvider(ModelProvider):
    name = "openrouter"

    def __init__(self, api_key: str | None = None) -> None:
        self.settings = get_settings()
        self.api_key = api_key or self.settings.openrouter_api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_referer,
            "X-Title": self.settings.openrouter_title,
        }

    def _extract_image_urls(self, raw_data: dict[str, Any]) -> list[str]:
        return list(
            _traverse_provider_response(
                raw_data,
                url_keys={"url", "image_url", "imageUrl"},
                container_keys={"images"},
            )
        )

    def _extract_video_urls(self, raw_data: dict[str, Any]) -> list[str]:
        return list(
            _traverse_provider_response(
                raw_data,
                url_keys={"url", "video_url", "videoUrl"},
                container_keys={"videos", "video_urls", "videoUrls"},
            )
        )

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise ProviderConfigurationError("OpenRouter")

    async def _post_json(
        self, path: str, payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        return await provider_post_json(
            provider_name="openrouter",
            url=f"{self.settings.openrouter_base_url}{path}",
            headers=self._headers,
            payload=payload,
            timeout=timeout,
        )

    async def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_api_key()
        raw_data = await self._post_json("/chat/completions", payload, timeout=300.0)

        normalized_images = [
            {"image_url": {"url": url}} for url in self._extract_image_urls(raw_data)
        ]

        return {
            "provider": "openrouter",
            "choices": [
                {
                    "message": {
                        "images": normalized_images,
                    }
                }
            ],
            "raw": raw_data,
        }

    async def generate_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_api_key()
        raw_data = await self._post_json("/chat/completions", payload, timeout=300.0)

        video_urls = self._extract_video_urls(raw_data)

        return {
            "provider": "openrouter",
            "videos": video_urls,
            "raw": raw_data,
        }

    async def generate_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_api_key()
        raw_data = await self._post_json("/chat/completions", payload, timeout=300.0)

        content = ""
        choices = raw_data.get("choices", [])
        if isinstance(choices, list) and choices:
            message = (
                choices[0].get("message") if isinstance(choices[0], dict) else None
            )
            if isinstance(message, dict):
                value = message.get("content")
                if isinstance(value, str):
                    content = value

        return {
            "provider": "openrouter",
            "text": content,
            "raw": raw_data,
        }

    async def get_models(self, output_modality: str = "image") -> dict[str, Any]:
        params = (
            None if output_modality == "all" else {"output_modality": output_modality}
        )
        return await provider_get_json(
            provider_name="openrouter",
            url=f"{self.settings.openrouter_base_url}/models",
            params=params,
        )
