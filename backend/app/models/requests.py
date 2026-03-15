from typing import Literal

from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    provider: Literal["openrouter", "openai"] = "openrouter"
    prompt: str = Field(min_length=1, max_length=5000)
    model: str = "google/gemini-2.5-flash-image-preview"
    aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = "1:1"
    image_size: Literal["1K", "2K", "4K"] = "1K"
    num_images: int = Field(default=1, ge=1, le=4)
    stream: bool = False


class ModelsQuery(BaseModel):
    provider: Literal["openrouter", "openai"] = "openrouter"
    output_modality: Literal["image", "text", "text,image"] = "image"
