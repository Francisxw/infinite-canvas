from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

import app.routers.openrouter as openrouter_router
from app.main import app
from app.models.requests import TextGenerationRequest, VideoGenerationRequest
from app.services.providers.base import ProviderUpstreamError


client = TestClient(app)


def test_text_generation_request_accepts_structured_prompt_parts() -> None:
    request = TextGenerationRequest.model_validate(
        {
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": [
                {"type": "text", "text": "describe this image"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.png",
                        "detail": "auto",
                    },
                },
            ],
        }
    )

    assert len(request.prompt) == 2


def test_text_generation_request_rejects_unknown_prompt_part_shape() -> None:
    try:
        TextGenerationRequest.model_validate(
            {
                "provider": "openrouter",
                "model": "google/gemini-2.5-flash",
                "prompt": [{"type": "broken", "value": "oops"}],
            }
        )
    except ValidationError as exc:
        assert "type" in str(exc)
    else:
        raise AssertionError("ValidationError was expected for invalid prompt part")


def test_generate_text_returns_safe_error_payload(monkeypatch) -> None:
    class FailingProvider:
        async def generate_text(self, payload):
            raise ProviderUpstreamError(
                "openrouter",
                code="http_error",
                message="The upstream provider request failed.",
            )

        async def generate_image(self, payload):
            raise NotImplementedError

        async def generate_video(self, payload):
            raise NotImplementedError

        async def get_models(self, output_modality="image"):
            raise NotImplementedError

    monkeypatch.setattr(
        openrouter_router,
        "get_provider",
        lambda provider: FailingProvider(),
    )

    response = client.post(
        "/api/generate-text",
        json={
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": "hello",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "openrouter_http_error",
            "message": "The upstream provider request failed.",
        }
    }


def test_video_generation_request_accepts_speed() -> None:
    request = VideoGenerationRequest.model_validate(
        {
            "provider": "openrouter",
            "model": "google/veo-3.1",
            "prompt": "slow motion fabric in the wind",
            "aspect_ratio": "16:9",
            "duration": "5s",
            "quality": "1080p",
            "speed": "fast",
        }
    )

    assert request.speed == "fast"


def test_generate_video_returns_safe_error_payload(monkeypatch) -> None:
    class FailingProvider:
        async def generate_text(self, payload):
            raise NotImplementedError

        async def generate_image(self, payload):
            raise NotImplementedError

        async def generate_video(self, payload):
            raise ProviderUpstreamError(
                "openrouter",
                code="video_generation_unsupported",
                message="Video generation is temporarily unavailable.",
            )

        async def get_models(self, output_modality="image"):
            raise NotImplementedError

    monkeypatch.setattr(
        openrouter_router,
        "get_provider",
        lambda provider: FailingProvider(),
    )

    response = client.post(
        "/api/generate-video",
        json={
            "provider": "openrouter",
            "model": "google/veo-3.1",
            "prompt": "paper sculpture unfolding",
            "aspect_ratio": "16:9",
            "duration": "5s",
            "quality": "1080p",
            "speed": "standard",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "openrouter_video_generation_unsupported",
            "message": "Video generation is temporarily unavailable.",
        }
    }


def test_generate_image_returns_safe_error_payload(monkeypatch) -> None:
    class FailingProvider:
        async def generate_text(self, payload):
            raise NotImplementedError

        async def generate_image(self, payload):
            raise ProviderUpstreamError(
                "openrouter",
                code="http_error",
                message="The upstream provider request failed.",
            )

        async def generate_video(self, payload):
            raise NotImplementedError

        async def get_models(self, output_modality="image"):
            raise NotImplementedError

    monkeypatch.setattr(
        openrouter_router,
        "get_provider",
        lambda provider: FailingProvider(),
    )

    response = client.post(
        "/api/generate-image",
        json={
            "provider": "openrouter",
            "model": "google/gemini-3.1-flash-image-preview",
            "prompt": "a sunset over mountains",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "openrouter_http_error",
            "message": "The upstream provider request failed.",
        }
    }


def test_generate_endpoints_accept_anonymous_requests() -> None:
    """Verify that generation endpoints no longer require authentication."""
    # These will fail with 502 because no real provider is configured,
    # but they should NOT return 401 (auth_required).
    response = client.post(
        "/api/generate-text",
        json={
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": "hello",
        },
    )
    # Any non-401 status code proves auth is no longer required.
    assert response.status_code != 401
