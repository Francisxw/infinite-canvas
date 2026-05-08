import logging
from typing import Literal

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.models.requests import (
    ImageGenerationRequest,
    TextGenerationRequest,
    VideoGenerationRequest,
)
from app.rate_limit import limiter
from app.routers.common import error_response
from app.services.providers.base import ProviderError
from app.services.providers.factory import get_provider

router = APIRouter(prefix="/api", tags=["openrouter"])
logger = logging.getLogger(__name__)


TEXT_IMAGE_MODELS = ("google/gemini-",)


def resolve_modalities(model: str) -> list[str]:
    normalized = model.lower()
    if normalized.startswith(TEXT_IMAGE_MODELS):
        return ["image", "text"]
    return ["image"]


def handle_generation_error(cost_type: str, exc: Exception) -> JSONResponse:
    """Convert generation errors into standardized error responses."""
    if isinstance(exc, ProviderError):
        return error_response(exc.status_code, exc.code, exc.message)
    return error_response(
        500, "internal_error", f"{cost_type.capitalize()} generation failed."
    )


@router.post("/generate-image")
@limiter.limit("60/minute")
async def generate_image(
    request: Request,
    payload: ImageGenerationRequest,
):
    provider_payload = {
        "model": payload.model,
        "messages": [{"role": "user", "content": payload.prompt}],
        "modalities": resolve_modalities(payload.model),
        "stream": payload.stream,
        "n": payload.num_images,
        "image_config": {
            "aspect_ratio": payload.aspect_ratio,
            "image_size": payload.image_size,
        },
    }

    try:
        client = get_provider(payload.provider)
        result = await client.generate_image(provider_payload)
    except (ProviderError, Exception) as exc:
        return handle_generation_error("image", exc)

    return JSONResponse(content=result)


@router.post("/generate-video")
@limiter.limit("60/minute")
async def generate_video(
    request: Request,
    payload: VideoGenerationRequest,
):
    provider_payload = {
        "model": payload.model,
        "messages": [{"role": "user", "content": payload.prompt}],
        "modalities": ["video"],
        "stream": payload.stream,
        "video_config": {
            "aspect_ratio": payload.aspect_ratio,
            "duration": payload.duration,
            "quality": payload.quality,
            "speed": payload.speed,
        },
    }

    try:
        client = get_provider(payload.provider)
        result = await client.generate_video(provider_payload)
    except (ProviderError, Exception) as exc:
        return handle_generation_error("video", exc)

    return JSONResponse(content=result)


@router.post("/generate-text")
@limiter.limit("60/minute")
async def generate_text(
    request: Request,
    payload: TextGenerationRequest,
):
    content = payload.prompt
    if isinstance(content, str):
        content = content.strip()
    else:
        content = [item.model_dump(exclude_none=True) for item in content]

    provider_payload = {
        "model": payload.model,
        "messages": [{"role": "user", "content": content}],
        "stream": False,
    }

    try:
        client = get_provider(payload.provider)
        result = await client.generate_text(provider_payload)
    except (ProviderError, Exception) as exc:
        return handle_generation_error("text", exc)

    return JSONResponse(content=result)


@router.get("/models")
@limiter.limit("120/minute")
async def list_models(
    request: Request,
    output_modality: str = Query(default="image"),
    provider: str = Query(default="openrouter"),
):
    try:
        client = get_provider(provider)
        result = await client.get_models(output_modality=output_modality)
    except ProviderError as exc:
        logger.warning("Model listing failed with %s", exc.code)
        return error_response(exc.status_code, exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected model listing failure")
        return error_response(500, "internal_error", "Model listing failed.")
    return result
