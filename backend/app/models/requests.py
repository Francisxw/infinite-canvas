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


class UserRegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=120)
    display_name: str = Field(min_length=2, max_length=40)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("email must be valid")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name must not be empty")
        return normalized


class UserLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=120)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("email must be valid")
        return normalized


class UpdateAccountSettingsRequest(BaseModel):
    openrouter_mode: Literal["platform", "custom"] = "platform"
    openrouter_api_key: str | None = Field(default=None, max_length=240)
    preferred_models: dict[Literal["text", "image", "video"], str | None] | None = None

    @field_validator("openrouter_api_key")
    @classmethod
    def normalize_api_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("preferred_models")
    @classmethod
    def normalize_preferred_models(
        cls, value: dict[Literal["text", "image", "video"], str | None] | None
    ) -> dict[Literal["text", "image", "video"], str | None] | None:
        if value is None:
            return None
        normalized: dict[Literal["text", "image", "video"], str | None] = {
            "text": None,
            "image": None,
            "video": None,
        }
        for key in normalized:
            raw = value.get(key)
            if raw is None:
                normalized[key] = None
                continue
            stripped = raw.strip()
            normalized[key] = stripped or None
        return normalized


class RechargeRequest(BaseModel):
    package_id: Literal["starter", "creator", "studio"]
    payment_reference: str = Field(min_length=8, max_length=120)

    @field_validator("payment_reference")
    @classmethod
    def normalize_payment_reference(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("payment_reference must not be empty")
        return normalized


class CreateWeChatRechargeOrderRequest(BaseModel):
    package_id: Literal["starter", "creator", "studio"]
