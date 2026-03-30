import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from app.models.requests import (
    ImageGenerationRequest,
    TextGenerationRequest,
    VideoGenerationRequest,
)
from app.rate_limit import limiter
from app.routers.common import error_response, require_user
from app.services.account_store import (
    AccountStoreError,
    GENERATION_COSTS,
    PublicUserRecord,
    account_store,
)
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


def success_response(payload: object, current_user: PublicUserRecord) -> JSONResponse:
    response = JSONResponse(content=payload)
    response.headers["X-Account-Points"] = str(current_user["points"])
    response.headers["X-Account-User-Id"] = str(current_user["id"])
    return response


@asynccontextmanager
async def consume_with_refund(
    user_id: str,
    cost_type: Literal["image", "video", "text"],
    description: str,
) -> AsyncGenerator[PublicUserRecord, None]:
    """Context manager that consumes points and refunds on failure.

    Yields the updated user record after consuming points.
    Automatically refunds points on cancellation or provider errors.
    """
    amount = GENERATION_COSTS[cost_type]
    try:
        current_user = account_store.consume_points(
            user_id=user_id,
            amount=amount,
            description=f"{cost_type.capitalize()} generation consumed points.",
        )
    except AccountStoreError as exc:
        raise

    try:
        yield current_user
    except asyncio.CancelledError:
        account_store.refund_points(
            user_id=user_id,
            amount=amount,
            description=f"{cost_type.capitalize()} generation cancelled, points refunded.",
        )
        raise
    except ProviderError as exc:
        account_store.refund_points(
            user_id=user_id,
            amount=amount,
            description=f"{cost_type.capitalize()} generation failed, points refunded.",
        )
        logger.warning("%s generation failed with %s", cost_type, exc.code)
        raise
    except Exception:
        account_store.refund_points(
            user_id=user_id,
            amount=amount,
            description=f"{cost_type.capitalize()} generation failed, points refunded.",
        )
        logger.exception("Unexpected %s generation failure", cost_type)
        raise


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
    current_user: PublicUserRecord = Depends(require_user),
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
        async with consume_with_refund(
            str(current_user["id"]), "image", payload.prompt
        ) as user:
            client = get_provider(payload.provider, user_id=str(user["id"]))
            result = await client.generate_image(provider_payload)
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except (ProviderError, Exception) as exc:
        return handle_generation_error("image", exc)

    return success_response(result, user)


@router.post("/generate-video")
@limiter.limit("60/minute")
async def generate_video(
    request: Request,
    payload: VideoGenerationRequest,
    current_user: PublicUserRecord = Depends(require_user),
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
        async with consume_with_refund(
            str(current_user["id"]), "video", payload.prompt
        ) as user:
            client = get_provider(payload.provider, user_id=str(user["id"]))
            result = await client.generate_video(provider_payload)
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except (ProviderError, Exception) as exc:
        return handle_generation_error("video", exc)

    return success_response(result, user)


@router.post("/generate-text")
@limiter.limit("60/minute")
async def generate_text(
    request: Request,
    payload: TextGenerationRequest,
    current_user: PublicUserRecord = Depends(require_user),
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
        async with consume_with_refund(
            str(current_user["id"]),
            "text",
            payload.prompt if isinstance(payload.prompt, str) else "Mixed content",
        ) as user:
            client = get_provider(payload.provider, user_id=str(user["id"]))
            result = await client.generate_text(provider_payload)
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except (ProviderError, Exception) as exc:
        return handle_generation_error("text", exc)

    return success_response(result, user)


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
