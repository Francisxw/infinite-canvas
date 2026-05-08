from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class ImageGenerationRequest(BaseModel):
    provider: Literal["openrouter", "openai"] = "openrouter"
    prompt: str = Field(min_length=1, max_length=5000)
    model: str = "google/gemini-3.1-flash-image-preview"
    aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = "1:1"
    image_size: Literal["1K", "2K", "4K"] = "1K"
    num_images: int = Field(default=1, ge=1, le=8)
    stream: bool = False


class VideoGenerationRequest(BaseModel):
    provider: Literal["openrouter", "openai"] = "openrouter"
    prompt: str = Field(min_length=1, max_length=5000)
    model: str = "google/veo-3.1"
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    duration: Literal["5s", "10s"] = "5s"
    quality: Literal["720p", "1080p"] = "1080p"
    speed: Literal["standard", "fast"] = "standard"
    stream: bool = False


class TextPromptPart(BaseModel):
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=5000)


class ImageUrlContent(BaseModel):
    url: str = Field(min_length=1)
    detail: Literal["low", "high", "auto"] = "auto"


class ImagePromptPart(BaseModel):
    type: Literal["image_url"]
    image_url: ImageUrlContent


PromptPart = Annotated[TextPromptPart | ImagePromptPart, Field(discriminator="type")]


class TextGenerationRequest(BaseModel):
    provider: Literal["openrouter", "openai"] = "openrouter"
    prompt: str | list[PromptPart]
    model: str = "google/gemini-2.5-flash"

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str | list[PromptPart]) -> str | list[PromptPart]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("prompt must not be empty")
            return stripped

        if len(value) == 0:
            raise ValueError("prompt must not be empty")

        return value


class ModelsQuery(BaseModel):
    provider: Literal["openrouter", "openai"] = "openrouter"
    output_modality: Literal["image", "video", "text", "text,image", "all"] = "image"
