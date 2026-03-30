from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx


class ProviderError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ProviderConfigurationError(ProviderError):
    def __init__(self, provider_name: str) -> None:
        super().__init__(
            f"{provider_name} is not configured.",
            code="provider_not_configured",
            status_code=503,
        )


class ProviderUpstreamError(ProviderError):
    def __init__(self, provider_name: str, *, code: str, message: str) -> None:
        super().__init__(message, code=f"{provider_name}_{code}", status_code=502)


async def provider_post_json(
    *,
    provider_name: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    """Shared HTTP JSON-POST helper for all model providers.

    Centralises httpx client creation, error handling and response
    parsing so individual providers don't duplicate this boilerplate.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise ProviderUpstreamError(
            provider_name,
            code="timeout",
            message="The upstream provider timed out.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise ProviderUpstreamError(
            provider_name,
            code="http_error",
            message="The upstream provider request failed.",
        ) from exc
    except httpx.HTTPError as exc:
        raise ProviderUpstreamError(
            provider_name,
            code="network_error",
            message="The upstream provider is unavailable.",
        ) from exc


async def provider_get_json(
    *,
    provider_name: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Shared HTTP GET helper for model providers (e.g. model listing)."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise ProviderUpstreamError(
            provider_name,
            code="timeout",
            message="The upstream provider timed out.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise ProviderUpstreamError(
            provider_name,
            code="http_error",
            message="The upstream provider request failed.",
        ) from exc
    except httpx.HTTPError as exc:
        raise ProviderUpstreamError(
            provider_name,
            code="network_error",
            message="The upstream provider is unavailable.",
        ) from exc


class ModelProvider(ABC):
    name: str

    @abstractmethod
    async def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_models(self, output_modality: str = "image") -> dict[str, Any]:
        raise NotImplementedError
