from typing import Any

import httpx

from app.config import get_settings


class OpenRouterClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Infinite Canvas",
        }

    async def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.openrouter_api_key:
            return {
                "success": False,
                "error": "OPENROUTER_API_KEY is not configured",
            }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.settings.openrouter_base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def get_models(self, output_modality: str = "image") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.settings.openrouter_base_url}/models",
                params={"output_modality": output_modality},
            )
            response.raise_for_status()
            return response.json()
