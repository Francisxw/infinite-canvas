from fastapi import APIRouter, HTTPException, Query

from app.models.requests import ImageGenerationRequest
from app.services.providers.factory import get_provider

router = APIRouter(prefix="/api", tags=["openrouter"])


TEXT_IMAGE_MODELS = ("google/gemini-",)


def resolve_modalities(model: str) -> list[str]:
    normalized = model.lower()
    if normalized.startswith(TEXT_IMAGE_MODELS):
        return ["image", "text"]
    return ["image"]


@router.post("/generate-image")
async def generate_image(request: ImageGenerationRequest):
    payload = {
        "model": request.model,
        "messages": [{"role": "user", "content": request.prompt}],
        "modalities": resolve_modalities(request.model),
        "stream": request.stream,
        "n": request.num_images,
        "image_config": {
            "aspect_ratio": request.aspect_ratio,
            "image_size": request.image_size,
        },
    }

    try:
        client = get_provider(request.provider)
        result = await client.generate_image(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"{type(exc).__name__}: {repr(exc)}"
        ) from exc

    return result


@router.get("/models")
async def list_models(
    output_modality: str = Query(default="image"),
    provider: str = Query(default="openrouter"),
):
    try:
        client = get_provider(provider)
        result = await client.get_models(output_modality=output_modality)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"{type(exc).__name__}: {repr(exc)}"
        ) from exc
    return result
