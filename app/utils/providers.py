import re

from fastapi import HTTPException

from app.core.config import get_ai_api_key, get_ai_base_url, get_chat_model


def selected_model(requested: str, fallback: str) -> str:
    model = (requested or fallback).strip()
    if not model:
        raise HTTPException(status_code=400, detail="模型名称不能为空")
    if len(model) > 120 or not re.fullmatch(r"[a-zA-Z0-9_.:/+-]+", model):
        raise HTTPException(status_code=400, detail=f"模型名称不合法：{model}")
    return model


def api_headers(json_body: bool = True) -> dict[str, str]:
    api_key = get_ai_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="未配置 COMFLY_API_KEY，请在 API/.env 中填写。")
    headers = {"Accept": "application/json", "Authorization": f"Bearer {api_key}"}
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def resolve_chat_provider(model: str):
    base = get_ai_base_url() + "/v1"
    headers = api_headers()
    resolved_model = selected_model(model, get_chat_model())
    return base, headers, resolved_model
