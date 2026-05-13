import json
import os
import re
import time
import uuid
from threading import Lock

from fastapi import HTTPException

from app.core.config import CANVAS_DIR, CANVAS_TRASH_RETENTION_MS


CANVAS_LOCK = Lock()


def _now_ms() -> int:
    return int(time.time() * 1000)


def canvas_path(canvas_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", canvas_id or "")
    if not cleaned:
        raise HTTPException(status_code=400, detail="无效的画布 ID")
    return os.path.join(CANVAS_DIR, f"{cleaned}.json")


def save_canvas(canvas: dict) -> None:
    canvas["updated_at"] = _now_ms()
    with CANVAS_LOCK:
        with open(canvas_path(canvas["id"]), "w", encoding="utf-8") as file:
            json.dump(canvas, file, ensure_ascii=False, indent=2)


def new_canvas(title: str = "未命名画布", icon: str = "layers") -> dict:
    timestamp = _now_ms()
    canvas = {
        "id": uuid.uuid4().hex,
        "title": (title or "未命名画布")[:80],
        "icon": (icon or "🧩")[:4],
        "created_at": timestamp,
        "updated_at": timestamp,
        "nodes": [],
        "connections": [],
        "viewport": {"x": 0, "y": 0, "scale": 1},
    }
    save_canvas(canvas)
    return canvas


def load_canvas(canvas_id: str) -> dict:
    path = canvas_path(canvas_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="画布不存在")
    with open(path, "r", encoding="utf-8") as file:
        canvas = json.load(file)
    if canvas.get("deleted_at"):
        raise HTTPException(status_code=404, detail="画布已在回收站")
    return canvas


def load_canvas_any(canvas_id: str) -> dict:
    path = canvas_path(canvas_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="画布不存在")
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _canvas_record(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "title": data.get("title", "未命名画布"),
        "icon": data.get("icon", "🧩"),
        "created_at": data.get("created_at", 0),
        "updated_at": data.get("updated_at", 0),
        "deleted_at": data.get("deleted_at", 0),
        "node_count": len(data.get("nodes", [])),
    }


def _cleanup_expired_canvas_trash() -> None:
    cutoff = _now_ms() - CANVAS_TRASH_RETENTION_MS
    with CANVAS_LOCK:
        for filename in os.listdir(CANVAS_DIR):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(CANVAS_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                deleted_at = int(data.get("deleted_at") or 0)
                if deleted_at and deleted_at < cutoff:
                    os.remove(path)
            except Exception:
                continue


def _iter_canvas_records(include_deleted: bool = False) -> list[dict]:
    _cleanup_expired_canvas_trash()
    records = []
    for filename in os.listdir(CANVAS_DIR):
        if not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(CANVAS_DIR, filename), "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception:
            continue
        is_deleted = bool(data.get("deleted_at"))
        if include_deleted != is_deleted:
            continue
        records.append(_canvas_record(data))
    return records


def list_canvases() -> list[dict]:
    return sorted(_iter_canvas_records(include_deleted=False), key=lambda item: item["updated_at"], reverse=True)


def list_deleted_canvases() -> list[dict]:
    return sorted(_iter_canvas_records(include_deleted=True), key=lambda item: item["deleted_at"], reverse=True)


def update_canvas(canvas_id: str, title: str, icon: str, nodes: list[dict], connections: list[dict], viewport: dict) -> dict:
    canvas = load_canvas(canvas_id)
    canvas["title"] = (title or canvas.get("title") or "未命名画布")[:80]
    canvas["icon"] = (icon or canvas.get("icon") or "layers")[:32]
    canvas["nodes"] = nodes
    canvas["connections"] = connections
    canvas["viewport"] = viewport
    save_canvas(canvas)
    return canvas


def delete_canvas(canvas_id: str) -> None:
    canvas = load_canvas_any(canvas_id)
    if not canvas.get("deleted_at"):
        canvas["deleted_at"] = _now_ms()
        save_canvas(canvas)


def restore_canvas(canvas_id: str) -> dict:
    canvas = load_canvas_any(canvas_id)
    if canvas.get("deleted_at"):
        canvas.pop("deleted_at", None)
        save_canvas(canvas)
    return canvas


def purge_canvas(canvas_id: str) -> None:
    path = canvas_path(canvas_id)
    if os.path.exists(path):
        os.remove(path)
