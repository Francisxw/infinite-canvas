import os

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import (
    API_ENV_FILE,
    CLIENT_ID,
    WORKFLOW_DIR,
)
from app.core.env_manager import env_settings, save_env_settings
from app.models.schemas import SettingsSaveRequest

router = APIRouter()

# Mapping from frontend-friendly keys to .env variable names
_ENV_KEY_MAP = {
    "comfly_base_url": "COMFLY_BASE_URL",
    "comfly_api_key": "COMFLY_API_KEY",
    "comfyui_instances": "COMFYUI_INSTANCES",
    "system_prompt": "SYSTEM_PROMPT",
    "max_history_messages": "MAX_HISTORY_MESSAGES",
    "request_timeout": "REQUEST_TIMEOUT",
    "image_poll_interval": "IMAGE_POLL_INTERVAL",
    "chat_models": "CHAT_MODELS",
    "image_models": "IMAGE_MODELS",
    "chat_model": "CHAT_MODEL",
    "image_model": "IMAGE_MODEL",
    "workflow_zimage": "WORKFLOW_ZIMAGE",
    "workflow_enhance": "WORKFLOW_ENHANCE",
    "workflow_upscale": "WORKFLOW_UPSCALE",
    "workflow_angle": "WORKFLOW_ANGLE",
    "workflow_klein": "WORKFLOW_KLEIN",
    "workflow_canvas_edit": "WORKFLOW_CANVAS_EDIT",
}

# Values that do NOT require an app restart (runtime-safe)
_RUNTIME_SAFE_KEYS = set(_ENV_KEY_MAP.keys())


class ComfyInstanceRequest(BaseModel):
    address: str = Field(..., description="ComfyUI 地址，如 127.0.0.1:8188")
    alias: str = Field(default="", description="可选别名")


class ComfyTestRequest(BaseModel):
    address: str = Field(..., description="要测试的 ComfyUI 地址")


def _queue_size(data: object, key: str) -> int:
    if not isinstance(data, dict):
        return 0
    value = data.get(key, [])
    return len(value) if isinstance(value, list) else 0


def _parse_env_value(key: str, raw: str):
    """Parse string .env values into their natural Python types."""
    if key in ("MAX_HISTORY_MESSAGES",):
        return int(raw)
    if key in ("REQUEST_TIMEOUT", "IMAGE_POLL_INTERVAL"):
        return float(raw)
    return raw


def _read_instances() -> list[str]:
    settings = env_settings(API_ENV_FILE)
    raw = settings.get("COMFYUI_INSTANCES", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _write_instances(instances: list[str]) -> None:
    value = ",".join(instances)
    save_env_settings(API_ENV_FILE, {"COMFYUI_INSTANCES": value})
    os.environ["COMFYUI_INSTANCES"] = value


def _probe_instance(address: str) -> dict[str, object]:
    status: dict[str, object] = {
        "address": address,
        "reachable": False,
        "queue_running": 0,
        "queue_pending": 0,
        "system_info": None,
    }
    try:
        response = requests.get(f"http://{address}/queue", timeout=3)
        if response.status_code == 200:
            data = response.json()
            status["reachable"] = True
            status["queue_running"] = _queue_size(data, "queue_running")
            status["queue_pending"] = _queue_size(data, "queue_pending")
    except Exception:
        pass
    try:
        response = requests.get(f"http://{address}/system_stats", timeout=3)
        if response.status_code == 200:
            status["system_info"] = response.json()
    except Exception:
        pass
    return status


def _settings_comfy_status(address: str) -> dict[str, object]:
    status = _probe_instance(address)
    return {
        "address": status["address"],
        "reachable": status["reachable"],
        "queue_running": status["queue_running"],
        "queue_pending": status["queue_pending"],
    }


@router.get("/api/settings")
def get_settings():
    """Return a safe summary of server settings.
    Exposes non-sensitive configuration for frontend consumption.
    """
    # Read the latest saved settings from disk so the frontend always sees
    # the most recently persisted values (especially for ComfyUI instances).
    file_settings = env_settings(API_ENV_FILE)

    comfy_instances = _read_instances() or ["127.0.0.1:8188"]

    # Environment summary (safe fields only)
    latest_api_key = file_settings.get("COMFLY_API_KEY", "").strip()
    env = {
        "client_id": CLIENT_ID,
        "comfy_instances": comfy_instances,
        "default_comfy": comfy_instances[0] if comfy_instances else "",
        "has_api_key": bool(latest_api_key),
    }

    # Build editable payload from the latest file values
    editable = {}
    for frontend_key, env_key in _ENV_KEY_MAP.items():
        raw = file_settings.get(env_key)
        editable[frontend_key] = _parse_env_value(env_key, raw) if raw is not None else ""

    # ComfyUI status per instance (uses latest saved instances)
    comfyui_status = [_settings_comfy_status(addr) for addr in comfy_instances]

    # List workflow JSON files
    try:
        workflows = [f for f in os.listdir(WORKFLOW_DIR) if f.lower().endswith('.json')]
    except Exception:
        workflows = []

    return {
        "env": env,
        "editable": editable,
        "comfyui_status": comfyui_status,
        "workflows": workflows,
    }


@router.post("/api/settings")
def save_settings(payload: SettingsSaveRequest):
    """Persist editable settings to API/.env.

    Returns a flag indicating whether the application must be restarted for
    the new values to take full effect (ComfyUI instances are runtime-safe).
    """
    updates: dict[str, str] = {}
    changed_runtime_sensitive = False

    for frontend_key, env_key in _ENV_KEY_MAP.items():
        value = getattr(payload, frontend_key, None)
        if value is not None:
            updates[env_key] = str(value)
            if frontend_key not in _RUNTIME_SAFE_KEYS:
                changed_runtime_sensitive = True

    if updates:
        save_env_settings(API_ENV_FILE, updates)
        # Also update os.environ so newly spawned processes see the change.
        for env_key, val in updates.items():
            os.environ[env_key] = val

    restart_required = changed_runtime_sensitive

    return {
        "success": True,
        "restart_required": restart_required,
    }


@router.get("/api/comfy/instances")
def list_instances() -> dict[str, object]:
    instances = [_probe_instance(addr) for addr in _read_instances()]
    return {"instances": instances, "count": len(instances)}


@router.post("/api/comfy/instances")
def add_instance(payload: ComfyInstanceRequest) -> dict[str, object]:
    address = payload.address.strip()
    if not address:
        raise HTTPException(status_code=400, detail="地址不能为空")

    instances = _read_instances()
    if address in instances:
        raise HTTPException(status_code=409, detail=f"实例 {address} 已存在")

    instances.append(address)
    _write_instances(instances)
    return {"success": True, "instances": instances, "added": _probe_instance(address)}


@router.put("/api/comfy/instances/{index}")
def update_instance(index: int, payload: ComfyInstanceRequest) -> dict[str, object]:
    instances = _read_instances()
    if index < 0 or index >= len(instances):
        raise HTTPException(status_code=404, detail=f"索引 {index} 超出范围")

    new_address = payload.address.strip()
    if not new_address:
        raise HTTPException(status_code=400, detail="地址不能为空")
    if new_address != instances[index] and new_address in instances:
        raise HTTPException(status_code=409, detail=f"实例 {new_address} 已存在")

    instances[index] = new_address
    _write_instances(instances)
    return {"success": True, "instances": instances, "updated": _probe_instance(new_address)}


@router.delete("/api/comfy/instances/{index}")
def delete_instance(index: int) -> dict[str, object]:
    instances = _read_instances()
    if index < 0 or index >= len(instances):
        raise HTTPException(status_code=404, detail=f"索引 {index} 超出范围")

    removed_address = instances.pop(index)
    _write_instances(instances)
    return {"success": True, "instances": instances, "removed_address": removed_address}


@router.post("/api/comfy/test")
def test_connection(payload: ComfyTestRequest) -> dict[str, object]:
    address = payload.address.strip()
    if not address:
        raise HTTPException(status_code=400, detail="地址不能为空")
    return _probe_instance(address)
