import json
import re

from app.utils.images import reference_to_data_url


def display_title(text: str) -> str:
    title = re.sub(r"\s+", " ", text or "").strip()
    return title[:24] or "新对话"


def _extract_text(content, joiner: str = "") -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text") or item.get("content") or "")
        return joiner.join(parts)
    return str(content) if content else ""


def text_from_chat_response(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return _extract_text(message.get("content", ""), "\n")


def text_delta_from_chat_chunk(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    return _extract_text(delta.get("content", ""))


def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def upstream_message_from_record(item: dict):
    role = item.get("role")
    if role not in {"user", "assistant"} or item.get("type") == "image":
        return None
    refs = item.get("attachments") or []
    if refs and role == "user":
        content = [{"type": "text", "text": item.get("content", "")}]
        for ref in refs[:4]:
            url = reference_to_data_url(ref)
            if url:
                content.append({"type": "image_url", "image_url": {"url": url}})
        return {"role": role, "content": content}
    return {"role": role, "content": item.get("content", "")}
