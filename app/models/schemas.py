from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from app.core.config import get_system_prompt, get_workflow_zimage


class GenerateRequest(BaseModel):
    prompt: str = ""
    width: int = 1024
    height: int = 1024
    workflow_json: str = Field(default_factory=get_workflow_zimage)
    params: Dict[str, Any] = {}
    type: str = "zimage"
    client_id: str = ""
    convert_to_jpg: bool = False


class DeleteHistoryRequest(BaseModel):
    timestamp: float


class TokenRequest(BaseModel):
    token: str


class CloudGenRequest(BaseModel):
    prompt: str
    api_key: str = ""
    resolution: str = "1024*1024"
    type: str = "zimage"
    image_urls: List[str] = []
    client_id: Optional[str] = None


class CloudPollRequest(BaseModel):
    task_id: str
    api_key: str = ""
    client_id: Optional[str] = None


class AIReference(BaseModel):
    url: str = ""
    name: str = ""


class OnlineImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    model: str = ""
    size: str = "1024x1024"
    quality: str = "auto"
    reference_images: List[AIReference] = []


class ChatRequest(BaseModel):
    conversation_id: str = ""
    message: str = Field(min_length=1, max_length=20000)
    model: str = ""
    image_model: str = ""
    mode: str = "chat"
    size: str = "1024x1024"
    quality: str = "auto"
    reference_images: List[AIReference] = []


class CanvasLLMRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    system_prompt: str = Field(default_factory=get_system_prompt)
    model: str = ""
    messages: List[Dict[str, str]] = []


class ConversationCreateRequest(BaseModel):
    title: str = "新对话"


class CanvasCreateRequest(BaseModel):
    title: str = "未命名画布"
    icon: str = "🧩"


class CanvasSaveRequest(BaseModel):
    title: str = "未命名画布"
    icon: str = "🧩"
    nodes: List[Dict[str, Any]] = []
    connections: List[Dict[str, Any]] = []
    viewport: Dict[str, Any] = {}


class SettingsSaveRequest(BaseModel):
    comfly_base_url: Optional[str] = None
    comfly_api_key: Optional[str] = None
    comfyui_instances: Optional[str] = None
    system_prompt: Optional[str] = None
    max_history_messages: Optional[int] = None
    request_timeout: Optional[float] = None
    image_poll_interval: Optional[float] = None
    chat_models: Optional[str] = None
    image_models: Optional[str] = None
    chat_model: Optional[str] = None
    image_model: Optional[str] = None
    workflow_zimage: Optional[str] = None
    workflow_enhance: Optional[str] = None
    workflow_upscale: Optional[str] = None
    workflow_angle: Optional[str] = None
    workflow_klein: Optional[str] = None
    workflow_canvas_edit: Optional[str] = None
