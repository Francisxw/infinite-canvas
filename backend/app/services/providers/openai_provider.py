from typing import Any

from app.config import get_settings
from app.services.providers.base import (
    ModelProvider,
    ProviderConfigurationError,
    ProviderError,
    provider_post_json,
)


class OpenAIProvider(ModelProvider):
    name = "openai"

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

    def _require_api_key(self) -> None:
        if not self.settings.openai_api_key:
            raise ProviderConfigurationError("OpenAI")

    async def _post_json(
        self, path: str, payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        return await provider_post_json(
            provider_name="openai",
            url=f"{self.settings.openai_base_url}{path}",
            headers=self._headers,
            payload=payload,
            timeout=timeout,
        )

    async def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_api_key()

        prompt = payload.get("messages", [{}])[0].get("content", "")
        model = payload.get("model", "gpt-image-1")
        image_size = payload.get("image_config", {}).get("image_size", "1K")

        size_map = {
            "1K": "1024x1024",
            "2K": "1536x1536",
            "4K": "2048x2048",
        }

        request_payload = {
            "model": model,
            "prompt": prompt,
            "size": size_map.get(image_size, "1024x1024"),
            "n": max(1, min(4, int(payload.get("n", 1)))),
        }

        data = await self._post_json(
            "/images/generations", request_payload, timeout=120.0
        )

        images = []
        for item in data.get("data", []):
            if item.get("b64_json"):
                images.append(
                    {"image_url": {"url": f"data:image/png;base64,{item['b64_json']}"}}
                )
            elif item.get("url"):
                images.append({"image_url": {"url": item["url"]}})

        return {
            "provider": "openai",
            "choices": [
                {
                    "message": {
                        "images": images,
                    }
                }
            ],
            "raw": data,
        }

    async def generate_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise ProviderError(
            "Video generation is not supported by the configured provider.",
            code="video_generation_unsupported",
            status_code=501,
        )

    async def generate_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_api_key()

        request_payload = {
            "model": payload.get("model", "gpt-4o-mini"),
            "messages": payload.get("messages", []),
        }

        data = await self._post_json(
            "/chat/completions", request_payload, timeout=120.0
        )

        content = ""
        choices = data.get("choices", [])
        if isinstance(choices, list) and choices:
            message = (
                choices[0].get("message") if isinstance(choices[0], dict) else None
            )
            if isinstance(message, dict):
                value = message.get("content")
                if isinstance(value, str):
                    content = value

        return {
            "provider": "openai",
            "text": content,
            "raw": data,
        }

    async def get_models(self, output_modality: str = "image") -> dict[str, Any]:
        return {
            "provider": "openai",
            "data": [
                {
                    "id": "gpt-image-1",
                    "name": "GPT Image 1",
                    "output_modality": output_modality,
                }
            ],
        }
