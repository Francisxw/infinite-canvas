import asyncio
from threading import Lock
from typing import TypedDict

from app.core.config import get_comfyui_instances


class QueueTask(TypedDict):
    task_id: int
    client_id: str


QUEUE: list[QueueTask] = []
QUEUE_LOCK = Lock()
LOAD_LOCK = Lock()
BACKEND_LOCAL_LOAD = {addr: 0 for addr in get_comfyui_instances()}
_next_task_id = 1
_global_loop: asyncio.AbstractEventLoop | None = None


def ensure_backend_local_load() -> dict[str, int]:
    instances = get_comfyui_instances()
    with LOAD_LOCK:
        for addr in instances:
            BACKEND_LOCAL_LOAD.setdefault(addr, 0)
        for addr in list(BACKEND_LOCAL_LOAD.keys()):
            if addr not in instances:
                BACKEND_LOCAL_LOAD.pop(addr, None)
        return dict(BACKEND_LOCAL_LOAD)


def set_global_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _global_loop
    _global_loop = loop


def reset_global_loop() -> None:
    global _global_loop
    _global_loop = None


def get_global_loop() -> asyncio.AbstractEventLoop | None:
    return _global_loop


def enqueue_task(client_id: str) -> QueueTask:
    global _next_task_id
    with QUEUE_LOCK:
        task_id = _next_task_id
        _next_task_id += 1
        current_task = {"task_id": task_id, "client_id": client_id}
        QUEUE.append(current_task)
    return current_task


def remove_task(current_task: QueueTask | None) -> None:
    if not current_task:
        return
    with QUEUE_LOCK:
        if current_task in QUEUE:
            QUEUE.remove(current_task)


def get_queue_status_for_client(client_id: str) -> dict[str, int]:
    with QUEUE_LOCK:
        total = len(QUEUE)
        positions = [index + 1 for index, task in enumerate(QUEUE) if task["client_id"] == client_id]
        position = positions[0] if positions else 0
    return {"total": total, "position": position}
