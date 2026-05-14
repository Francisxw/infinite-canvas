import json
import os
import re
import uuid
from typing import Optional

import requests
from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

from app.core.config import OUTPUT_DIR, STATIC_DIR, get_ai_api_key, get_ai_base_url, get_chat_model, get_chat_models, get_comfyui_instances, get_image_model, get_image_models
from app.utils.images import content_type_for_path, output_file_from_url
from app.ws.manager import manager


router = APIRouter()

_VIEW_TYPES = {"input", "output", "temp"}
_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
_SAFE_SUBFOLDER_RE = re.compile(r"^[a-zA-Z0-9_./-]*$")


def _validate_view_filename(filename: str) -> str:
    raw = (filename or "").strip()
    cleaned = os.path.basename(raw)
    if not cleaned or cleaned != raw or not _SAFE_FILENAME_RE.fullmatch(cleaned):
        raise HTTPException(status_code=400, detail="无效的文件名")
    return cleaned


def _validate_view_subfolder(subfolder: str) -> str:
    cleaned = (subfolder or "").strip().replace("\\", "/")
    invalid = (
        cleaned.startswith("/")
        or any(part == ".." for part in cleaned.split("/"))
        or not _SAFE_SUBFOLDER_RE.fullmatch(cleaned)
    )
    if invalid:
        raise HTTPException(status_code=400, detail="无效的子目录")
    return cleaned


@router.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        await manager.disconnect(websocket, client_id)
    except Exception as exc:
        print(f"WS Error: {exc}")
        await manager.disconnect(websocket, client_id)


@router.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@router.get("/api/view")
def view_image(filename: str, type: str = "input", subfolder: str = ""):
    filename = _validate_view_filename(filename)
    if type not in _VIEW_TYPES:
        raise HTTPException(status_code=400, detail="无效的图片类型")
    subfolder = _validate_view_subfolder(subfolder)
    for addr in get_comfyui_instances():
        try:
            url = f"http://{addr}/view"
            params = {"filename": filename, "type": type, "subfolder": subfolder}
            response = requests.get(url, params=params, timeout=1)
            if response.status_code == 200:
                return Response(content=response.content, media_type=response.headers.get("Content-Type"))
        except Exception:
            continue
    raise HTTPException(status_code=404, detail="Image not found on any available backend")


@router.get("/api/download-output")
def download_output(url: str, name: str = ""):
    path = output_file_from_url(url)
    if not path:
        raise HTTPException(status_code=404, detail="文件不存在")
    filename = os.path.basename(name) if name else os.path.basename(path)
    return FileResponse(path, media_type=content_type_for_path(path), filename=filename)


@router.post("/api/upload")
async def upload_image(files: list[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        content = await file.read()
        success_count = 0
        last_result = None
        for addr in get_comfyui_instances():
            try:
                files_data = {"image": (file.filename, content, file.content_type)}
                response = requests.post(f"http://{addr}/upload/image", files=files_data, timeout=5)
                if response.status_code == 200:
                    last_result = response.json()
                    success_count += 1
            except Exception as exc:
                print(f"Upload error for {addr}: {exc}")

        if not success_count or not last_result:
            raise HTTPException(status_code=500, detail="Failed to upload to any backend")
        uploaded_files.append({"comfy_name": last_result.get("name", file.filename)})

    return {"files": uploaded_files}


@router.post("/api/ai/upload")
async def upload_ai_reference(files: list[UploadFile] = File(...)):
    uploaded = []
    for file in files:
        content = await file.read()
        if not content:
            continue
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            content_type = (file.content_type or "").lower()
            ext = ".jpg" if "jpeg" in content_type else ".webp" if "webp" in content_type else ".png"
        filename = f"ai_ref_{uuid.uuid4().hex[:12]}{ext}"
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "wb") as file_handle:
            file_handle.write(content)
        uploaded.append({"url": f"/output/{filename}", "name": file.filename or filename})
    return {"files": uploaded}


@router.get("/api/config")
async def ai_config():
    chat_models = get_chat_models()
    fallback = chat_models[0] if chat_models else get_chat_model()
    preferred_chat_model = next((model for model in chat_models if model == "gpt-5.5"), fallback)
    return {
        "base_url": get_ai_base_url(),
        "chat_model": preferred_chat_model,
        "image_model": get_image_model(),
        "chat_models": chat_models,
        "image_models": get_image_models(),
        "has_api_key": bool(get_ai_api_key()),
    }


@router.get("/api/models")
async def ai_models():
    return {"chat_models": get_chat_models(), "image_models": get_image_models()}


@router.get("/api/config/token")
async def get_global_token():
    return {"token": ""}
