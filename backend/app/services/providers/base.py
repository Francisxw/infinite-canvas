from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    name: str

    @abstractmethod
    async def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_models(self, output_modality: str = "image") -> dict[str, Any]:
        raise NotImplementedError
