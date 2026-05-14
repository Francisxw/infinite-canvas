import json
import os
import time
from threading import Lock
from typing import Optional

from app.core.config import HISTORY_FILE, OUTPUT_DIR


HISTORY_LOCK = Lock()


def save_to_history(record: dict) -> None:
    with HISTORY_LOCK:
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                    history = json.load(file)
            except Exception:
                pass
        if "timestamp" not in record:
            record["timestamp"] = time.time()
        history.insert(0, record)
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history[:5000], file, ensure_ascii=False, indent=4)


def get_history(item_type: Optional[str] = None) -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if item_type:
            data = [item for item in data if item.get("type", "zimage") == item_type]
        data = [item for item in data if item.get("images") and len(item["images"]) > 0]

        data.sort(key=lambda item: float(item.get("timestamp", 0)) if isinstance(item.get("timestamp"), (int, float)) else 0, reverse=True)
        return data
    except Exception as exc:
        print(f"读取历史文件失败: {exc}")
        return []


def _timestamps_match(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 0.001
    return str(a) == str(b)


def delete_history_entry(timestamp: float) -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {"success": False, "message": "History file not found"}
    try:
        with HISTORY_LOCK:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                history = json.load(file)
            target_record = None
            new_history = []
            for item in history:
                if _timestamps_match(timestamp, item.get("timestamp", 0)):
                    target_record = item
                else:
                    new_history.append(item)
            if target_record:
                with open(HISTORY_FILE, "w", encoding="utf-8") as file:
                    json.dump(new_history, file, ensure_ascii=False, indent=4)

        if not target_record:
            return {"success": False, "message": "Record not found"}

        for image_url in target_record.get("images", []):
            if not image_url.startswith("/output/"):
                continue
            file_path = os.path.join(OUTPUT_DIR, os.path.basename(image_url.split("?", 1)[0]))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as exc:
                    print(f"Failed to delete file {file_path}: {exc}")
        return {"success": True}
    except Exception as exc:
        print(f"Delete history error: {exc}")
        return {"success": False, "message": str(exc)}
