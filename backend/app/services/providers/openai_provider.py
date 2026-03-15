from typing import Any

import httpx

from app.config import get_settings
from app.services.providers.base import ModelProvider


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

    async def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY is not configured",
            }

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

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.settings.openai_base_url}/images/generations",
                headers=self._headers,
                json=request_payload,
            )
            response.raise_for_status()
            data = response.json()

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
