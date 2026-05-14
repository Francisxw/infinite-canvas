import asyncio
import json
import os
import random
import urllib.error
import urllib.parse

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import WORKFLOW_DIR, get_comfyui_instances, get_workflow_path, get_workflow_zimage
from app.models.schemas import GenerateRequest
from app.runtime import BACKEND_LOCAL_LOAD, LOAD_LOCK, ensure_backend_local_load, get_global_loop, enqueue_task, remove_task
from app.services.history_service import save_to_history
from app.utils.backend import get_best_backend
from app.utils.images import convert_output_to_jpg, download_image
from app.ws.manager import manager


router = APIRouter()


def _collect_required_images(params: dict) -> list[str]:
    """从请求参数中提取需要同步的图像名称。"""
    required_images = []
    for node_inputs in params.values():
        if not isinstance(node_inputs, dict):
            continue
        image_name = node_inputs.get("image")
        if isinstance(image_name, str) and image_name:
            required_images.append(image_name)
    return required_images


def _inject_workflow_params(workflow: dict, req: GenerateRequest, seed: int) -> None:
    """根据 class_type 自动注入画布参数，不再硬编码节点 ID。"""
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs", {})
        class_type = node.get("class_type", "")

        # 1) Prompt 注入
        if req.prompt and class_type in {"CLIPTextEncode", "ShowText", "PromptText"}:
            if "text" in inputs:
                inputs["text"] = req.prompt
            if "string" in inputs:
                inputs["string"] = req.prompt

        # 2) 尺寸注入 —— 只注入直接数字值，跳过引用数组
        if class_type in {"EmptyLatentImage", "EmptySD3LatentImage", "EmptyFlux2LatentImage"}:
            if "width" in inputs and isinstance(inputs["width"], (int, float)):
                inputs["width"] = req.width
            if "height" in inputs and isinstance(inputs["height"], (int, float)):
                inputs["height"] = req.height

        # 3) Seed 注入
        if class_type in {
            "KSampler", "KSamplerAdvanced", "SamplerCustomAdvanced",
            "SeedVR2VideoUpscaler", "RandomNoise",
        }:
            if "seed" in inputs and isinstance(inputs["seed"], (int, float)):
                inputs["seed"] = seed
            if "noise_seed" in inputs and isinstance(inputs["noise_seed"], (int, float)):
                inputs["noise_seed"] = seed


def _apply_user_params(workflow: dict, params: dict) -> None:
    """将用户请求中的节点参数覆盖到工作流。"""
    for node_id, node_inputs in params.items():
        if node_id not in workflow:
            continue
        workflow[node_id].setdefault("inputs", {})
        for input_name, value in node_inputs.items():
            workflow[node_id]["inputs"][input_name] = value


async def _sync_image(client: httpx.AsyncClient, image_name: str, target_backend: str) -> None:
    """如果目标后端缺少输入图像，从其他后端同步过来。"""
    check_url = f"http://{target_backend}/view?filename={urllib.parse.quote(image_name)}&type=input"
    try:
        response = await client.get(check_url, timeout=0.5)
        if response.status_code == 200:
            return
    except httpx.HTTPError:
        pass

    image_content = None
    image_type = "image/png"
    for addr in get_comfyui_instances():
        if addr == target_backend:
            continue
        src_url = f"http://{addr}/view?filename={urllib.parse.quote(image_name)}&type=input"
        try:
            response = await client.get(src_url, timeout=5.0)
            if response.status_code == 200:
                image_content = response.content
                image_type = response.headers.get("Content-Type", "image/png")
                break
        except httpx.HTTPError:
            continue

    if image_content is None:
        return

    try:
        files = {"image": (image_name, image_content, image_type)}
        await client.post(f"http://{target_backend}/upload/image", files=files, timeout=10.0)
    except httpx.HTTPError as exc:
        print(f"Sync upload failed: {exc}")


async def _wait_for_history(client: httpx.AsyncClient, target_backend: str, prompt_id: str) -> dict | None:
    """轮询等待 ComfyUI 完成渲染并返回历史记录。"""
    for _ in range(300):
        try:
            response = await client.get(f"http://{target_backend}/history/{prompt_id}", timeout=10.0)
            response.raise_for_status()
            history_response = response.json()
            if isinstance(history_response, dict) and prompt_id in history_response:
                return history_response[prompt_id]
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"查询 ComfyUI 历史记录失败：{exc.response.text}",
            ) from exc
        except httpx.HTTPError:
            pass
        await asyncio.sleep(1)
    return None


async def _process_outputs(
    history_data: dict,
    target_backend: str,
    req: GenerateRequest,
    current_timestamp: float,
) -> list[str]:
    """从历史记录中提取输出图像并下载到本地。"""
    local_urls = []
    outputs = history_data.get("outputs") if isinstance(history_data, dict) else None
    if not isinstance(outputs, dict):
        return local_urls

    for node_output in outputs.values():
        if not isinstance(node_output, dict):
            continue
        images = node_output.get("images")
        if not isinstance(images, list):
            continue
        for image in images:
            if not isinstance(image, dict):
                continue
            filename = image.get("filename")
            image_type = image.get("type")
            if not isinstance(filename, str) or not isinstance(image_type, str):
                continue
            subfolder = image.get("subfolder", "")
            comfy_url_path = f"/view?filename={filename}&subfolder={subfolder}&type={image_type}"
            prefix = f"{req.type}_{int(current_timestamp)}_"
            local_path = await asyncio.to_thread(download_image, target_backend, comfy_url_path, prefix)
            if req.convert_to_jpg:
                local_path = await asyncio.to_thread(convert_output_to_jpg, local_path)
            local_urls.append(local_path)

    return local_urls


def _build_result(req: GenerateRequest, local_urls: list[str], seed: int, timestamp: float) -> dict:
    """组装最终返回结果。"""
    return {
        "prompt": req.prompt or "Detail Enhance",
        "images": local_urls,
        "seed": seed,
        "timestamp": timestamp,
        "type": req.type,
        "params": req.params,
    }


@router.post("/api/generate")
async def generate(req: GenerateRequest):
    current_task = enqueue_task(req.client_id)
    target_backend = None

    try:
        ensure_backend_local_load()
        required_images = _collect_required_images(req.params)
        target_backend = await asyncio.to_thread(get_best_backend, required_images, BACKEND_LOCAL_LOAD, LOAD_LOCK)
        with LOAD_LOCK:
            BACKEND_LOCAL_LOAD[target_backend] += 1

        workflow_name = req.workflow_json or get_workflow_zimage()
        workflow_path = os.path.join(WORKFLOW_DIR, workflow_name)
        if not os.path.exists(workflow_path) and workflow_name == get_workflow_zimage():
            workflow_path = get_workflow_path()
        if not os.path.exists(workflow_path):
            raise HTTPException(status_code=404, detail=f"工作流文件不存在：{workflow_name}")

        with open(workflow_path, "r", encoding="utf-8") as file:
            workflow = json.load(file)

        seed = random.randint(1, 10**15)
        _inject_workflow_params(workflow, req, seed)
        _apply_user_params(workflow, req.params)

        async with httpx.AsyncClient() as client:
            for image_name in required_images:
                await _sync_image(client, image_name, target_backend)

            payload = {"prompt": workflow, "client_id": req.client_id}
            try:
                response = await client.post(f"http://{target_backend}/prompt", json=payload, timeout=10.0)
                response.raise_for_status()
                prompt_id = response.json().get("prompt_id")
            except httpx.HTTPStatusError as exc:
                raise HTTPException(status_code=exc.response.status_code, detail=f"ComfyUI 请求失败：{exc.response.text}") from exc
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"请求 ComfyUI 失败：{exc}") from exc

            if not prompt_id:
                raise HTTPException(status_code=502, detail="ComfyUI 未返回 prompt_id")

            history_data = await _wait_for_history(client, target_backend, prompt_id)

        if not history_data:
            raise HTTPException(status_code=504, detail="ComfyUI 渲染超时")

        current_timestamp = asyncio.get_running_loop().time()
        local_urls = await _process_outputs(history_data, target_backend, req, current_timestamp)
        result = _build_result(req, local_urls, seed, current_timestamp)
        save_to_history(result)
        loop = get_global_loop()
        if loop:
            asyncio.run_coroutine_threadsafe(manager.broadcast_new_image(result), loop)
        return result
    except HTTPException:
        raise
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=exc.code, detail=f"ComfyUI 请求失败：{error_body}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成失败：{exc}") from exc
    finally:
        if target_backend:
            with LOAD_LOCK:
                if BACKEND_LOCAL_LOAD.get(target_backend, 0) > 0:
                    BACKEND_LOCAL_LOAD[target_backend] -= 1
        remove_task(current_task)
