import json
import urllib.parse
import urllib.request
from threading import Lock
from typing import Optional

import requests

from app.core.config import get_comfyui_instances


def check_images_exist(backend_addr: str, images: list[str] | None) -> bool:
    if not images:
        return True
    for image_name in images:
        try:
            url = f"http://{backend_addr}/view?filename={urllib.parse.quote(image_name)}&type=input"
            response = requests.get(url, stream=True, timeout=0.5)
            response.close()
            if response.status_code != 200:
                return False
        except Exception:
            return False
    return True


def get_best_backend(required_images: list[str] | None = None, backend_local_load: Optional[dict[str, int]] = None, load_lock: Optional[Lock] = None) -> str:
    instances = get_comfyui_instances()
    best_backend = instances[0]
    min_queue_size = float("inf")
    candidates_with_images = []
    candidates_others = []
    backend_stats = {}

    for addr in instances:
        try:
            with urllib.request.urlopen(f"http://{addr}/queue", timeout=1) as response:
                data = json.loads(response.read())
                remote_load = len(data.get("queue_running", [])) + len(data.get("queue_pending", []))
                if load_lock and backend_local_load is not None:
                    with load_lock:
                        local_load = backend_local_load.get(addr, 0)
                else:
                    local_load = (backend_local_load or {}).get(addr, 0)
                effective_load = max(remote_load, local_load)
                has_images = check_images_exist(addr, required_images)
                backend_stats[addr] = {"load": effective_load, "has_images": has_images}
                if has_images:
                    candidates_with_images.append(addr)
                else:
                    candidates_others.append(addr)
        except Exception as exc:
            print(f"Backend {addr} unreachable: {exc}")
            continue

    target_candidates = candidates_with_images if candidates_with_images else candidates_others
    if not target_candidates:
        if candidates_others:
            target_candidates = candidates_others
        else:
            return instances[0]

    for addr in target_candidates:
        load = backend_stats[addr]["load"]
        if load < min_queue_size:
            min_queue_size = load
            best_backend = addr

    return best_backend


def get_comfy_history(comfy_address: str, prompt_id: str) -> dict[str, object]:
    try:
        with urllib.request.urlopen(f"http://{comfy_address}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except Exception:
        return {}
