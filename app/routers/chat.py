import asyncio
import json
import time
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.config import get_ai_request_timeout, get_image_model, get_max_history_messages, get_system_prompt
from app.models.schemas import CanvasLLMRequest, ChatRequest, OnlineImageRequest
from app.runtime import get_global_loop
from app.services.conversation_service import load_conversation, new_conversation, now_ms, safe_user_id, save_conversation
from app.services.history_service import save_to_history
from app.utils.chat import display_title, sse_event, text_delta_from_chat_chunk, text_from_chat_response, upstream_message_from_record
from app.utils.images import generate_ai_image, save_ai_image_to_output
from app.utils.providers import resolve_chat_provider, selected_model
from app.ws.manager import manager


router = APIRouter()


def _upsert_conversation(user_id: str, conversation_id: str, message: str) -> dict:
    conversation = load_conversation(user_id, conversation_id) if conversation_id else new_conversation(user_id, display_title(message))
    if not conversation.get("messages"):
        conversation["title"] = display_title(message)
    return conversation


def _append_user_message(conversation: dict, payload: ChatRequest) -> None:
    refs = [ref.dict() for ref in payload.reference_images if ref.url]
    conversation["messages"].append({
        "id": uuid.uuid4().hex,
        "role": "user",
        "content": payload.message,
        "created_at": now_ms(),
        "attachments": refs,
        "mode": payload.mode,
    })
    conversation["updated_at"] = now_ms()


def _build_upstream_messages(history: list[dict]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": get_system_prompt()}]
    for item in history:
        msg = upstream_message_from_record(item)
        if msg:
            messages.append(msg)
    return messages


async def _call_chat(chat_base: str, chat_hdrs: dict, model: str, messages: list) -> dict:
    async with httpx.AsyncClient(timeout=get_ai_request_timeout()) as client:
        response = await client.post(
            f"{chat_base}/chat/completions",
            headers=chat_hdrs,
            json={"model": model, "messages": messages},
        )
        response.raise_for_status()
        return response.json()


def _http_error_from_httpx(exc: httpx.HTTPStatusError, prefix: str) -> HTTPException:
    return HTTPException(status_code=exc.response.status_code, detail=f"{prefix}：{exc.response.text}")


def _http_error_generic(exc: httpx.HTTPError, prefix: str) -> HTTPException:
    return HTTPException(status_code=502, detail=f"{prefix}：{exc}")


@router.post("/api/online-image")
async def online_image(payload: OnlineImageRequest):
    model = selected_model(payload.model, get_image_model())
    refs = [ref.dict() for ref in payload.reference_images if ref.url]
    try:
        image_data, raw = await generate_ai_image(payload.prompt, payload.size, payload.quality, model, refs)
        local_url = await save_ai_image_to_output(image_data, prefix="online_")
    except httpx.HTTPStatusError as exc:
        raise _http_error_from_httpx(exc, "上游生图接口错误")
    except httpx.HTTPError as exc:
        raise _http_error_generic(exc, "请求上游生图接口失败")

    result = {
        "prompt": payload.prompt,
        "images": [local_url],
        "timestamp": time.time(),
        "type": "online",
        "model": model,
        "params": {"model": model, "size": payload.size, "quality": payload.quality, "reference_images": refs},
        "raw_usage": raw.get("usage") if isinstance(raw, dict) else None,
    }
    save_to_history(result)
    loop = get_global_loop()
    if loop:
        asyncio.run_coroutine_threadsafe(manager.broadcast_new_image(result), loop)
    return result


@router.post("/api/canvas-llm")
async def canvas_llm(payload: CanvasLLMRequest):
    chat_base, chat_hdrs, model = resolve_chat_provider(payload.model)
    upstream_messages: list[dict[str, Any]] = [{"role": "system", "content": payload.system_prompt or get_system_prompt()}]
    for item in payload.messages[-get_max_history_messages():]:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and content:
            upstream_messages.append({"role": role, "content": content})
    upstream_messages.append({"role": "user", "content": payload.message})
    try:
        raw = await _call_chat(chat_base, chat_hdrs, model, upstream_messages)
    except httpx.HTTPStatusError as exc:
        raise _http_error_from_httpx(exc, "上游接口错误")
    except httpx.HTTPError as exc:
        raise _http_error_generic(exc, "请求上游接口失败")
    text = text_from_chat_response(raw).strip() or "接口返回了空回复。"
    return {"text": text, "model": model, "raw_usage": raw.get("usage") if isinstance(raw, dict) else None}


@router.post("/api/chat")
async def chat(payload: ChatRequest, request: Request, x_user_id: str = Header(default="")):
    user_id = safe_user_id(x_user_id, request)
    conversation = _upsert_conversation(user_id, payload.conversation_id, payload.message)
    _append_user_message(conversation, payload)
    save_conversation(user_id, conversation)

    if payload.mode == "image":
        model = selected_model(payload.image_model or payload.model, get_image_model())
        refs = [ref.dict() for ref in payload.reference_images if ref.url]
        try:
            image_data, raw = await generate_ai_image(payload.message, payload.size, payload.quality, model, refs)
            local_url = await save_ai_image_to_output(image_data, prefix="chat_")
        except httpx.HTTPStatusError as exc:
            raise _http_error_from_httpx(exc, "上游生图接口错误")
        except httpx.HTTPError as exc:
            raise _http_error_generic(exc, "请求上游生图接口失败")
        assistant_message = {
            "id": uuid.uuid4().hex,
            "role": "assistant",
            "type": "image",
            "content": payload.message,
            "image_url": local_url,
            "created_at": now_ms(),
            "model": model,
            "raw_usage": raw.get("usage") if isinstance(raw, dict) else None,
        }
    else:
        chat_base, chat_hdrs, model = resolve_chat_provider(payload.model)
        upstream_messages = _build_upstream_messages(conversation["messages"][-get_max_history_messages():])
        try:
            raw = await _call_chat(chat_base, chat_hdrs, model, upstream_messages)
        except httpx.HTTPStatusError as exc:
            raise _http_error_from_httpx(exc, "上游接口错误")
        except httpx.HTTPError as exc:
            raise _http_error_generic(exc, "请求上游接口失败")
        assistant_message = {
            "id": uuid.uuid4().hex,
            "role": "assistant",
            "content": text_from_chat_response(raw).strip() or "接口返回了空回复。",
            "created_at": now_ms(),
            "model": model,
            "raw_usage": raw.get("usage") if isinstance(raw, dict) else None,
        }

    conversation["messages"].append(assistant_message)
    conversation["updated_at"] = now_ms()
    save_conversation(user_id, conversation)
    return {"conversation": conversation, "message": assistant_message}


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, request: Request, x_user_id: str = Header(default="")):
    if payload.mode == "image":
        raise HTTPException(status_code=400, detail="图片模式请使用 /api/chat")

    user_id = safe_user_id(x_user_id, request)
    conversation = _upsert_conversation(user_id, payload.conversation_id, payload.message)
    _append_user_message(conversation, payload)
    save_conversation(user_id, conversation)

    chat_base, chat_hdrs, model = resolve_chat_provider(payload.model)
    upstream_messages = _build_upstream_messages(conversation["messages"][-get_max_history_messages():])

    async def stream():
        content_parts = []
        raw_usage = None
        yield sse_event({"type": "meta", "conversation": conversation})
        try:
            async with httpx.AsyncClient(timeout=get_ai_request_timeout()) as client:
                async with client.stream(
                    "POST",
                    f"{chat_base}/chat/completions",
                    headers=chat_hdrs,
                    json={"model": model, "messages": upstream_messages, "stream": True},
                ) as response:
                    if response.status_code >= 400:
                        detail = await response.aread()
                        yield sse_event({"type": "error", "detail": f"上游接口错误：{detail.decode('utf-8', errors='ignore')}"})
                        return
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data:"):
                            line = line[5:].strip()
                        if line == "[DONE]":
                            break
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(chunk, dict) and chunk.get("usage"):
                            raw_usage = chunk.get("usage")
                        delta = text_delta_from_chat_chunk(chunk)
                        if delta:
                            content_parts.append(delta)
                            yield sse_event({"type": "delta", "delta": delta})
        except httpx.HTTPError as exc:
            yield sse_event({"type": "error", "detail": f"请求上游接口失败：{exc}"})
            return

        assistant_message = {
            "id": uuid.uuid4().hex,
            "role": "assistant",
            "content": "".join(content_parts).strip() or "接口返回了空回复。",
            "created_at": now_ms(),
            "model": model,
            "raw_usage": raw_usage,
        }
        conversation["messages"].append(assistant_message)
        conversation["updated_at"] = now_ms()
        save_conversation(user_id, conversation)
        yield sse_event({"type": "done", "conversation": conversation, "message": assistant_message})

    return StreamingResponse(stream(), media_type="text/event-stream")
