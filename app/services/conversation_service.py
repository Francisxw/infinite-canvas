import json
import os
import re
import time
import uuid
from threading import Lock

from fastapi import HTTPException, Request

from app.core.config import CONVERSATION_DIR


CONVERSATION_LOCK = Lock()


def now_ms() -> int:
    return int(time.time() * 1000)


def safe_user_id(user_id: str, request: Request) -> str:
    candidate = (user_id or "").strip()
    if not candidate and request.client:
        candidate = f"ip-{request.client.host}"
    if not candidate:
        candidate = "anonymous"
    candidate = re.sub(r"[^a-zA-Z0-9_.-]", "-", candidate)[:80].strip(".-")
    return candidate or "anonymous"


def user_dir(user_id: str) -> str:
    path = os.path.join(CONVERSATION_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def conversation_path(user_id: str, conversation_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", conversation_id or "")
    if not cleaned:
        raise HTTPException(status_code=400, detail="无效的对话 ID")
    return os.path.join(user_dir(user_id), f"{cleaned}.json")


def save_conversation(user_id: str, conversation: dict) -> None:
    with CONVERSATION_LOCK:
        path = conversation_path(user_id, conversation["id"])
        with open(path, "w", encoding="utf-8") as file:
            json.dump(conversation, file, ensure_ascii=False, indent=2)


def new_conversation(user_id: str, title: str = "新对话") -> dict:
    timestamp = now_ms()
    conversation = {
        "id": uuid.uuid4().hex,
        "title": (title or "新对话")[:80],
        "created_at": timestamp,
        "updated_at": timestamp,
        "messages": [],
    }
    save_conversation(user_id, conversation)
    return conversation


def load_conversation(user_id: str, conversation_id: str) -> dict:
    path = conversation_path(user_id, conversation_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="对话不存在")
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def list_conversations(user_id: str) -> list[dict]:
    records = []
    current_user_dir = user_dir(user_id)
    for filename in os.listdir(current_user_dir):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(current_user_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception:
            continue
        messages = data.get("messages", [])
        last_message = next((message for message in reversed(messages) if message.get("role") != "system"), None)
        records.append(
            {
                "id": data.get("id"),
                "title": data.get("title", "新对话"),
                "created_at": data.get("created_at", 0),
                "updated_at": data.get("updated_at", 0),
                "last_message": (last_message or {}).get("content", ""),
            }
        )
    return sorted(records, key=lambda item: item["updated_at"], reverse=True)


def delete_conversation(user_id: str, conversation_id: str) -> None:
    path = conversation_path(user_id, conversation_id)
    if os.path.exists(path):
        os.remove(path)
