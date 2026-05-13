import asyncio
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request

import requests
from fastapi import APIRouter

from app.core.config import WORKFLOW_DIR, get_comfyui_instances, get_workflow_path, get_workflow_zimage
from app.models.schemas import GenerateRequest
from app.runtime import BACKEND_LOCAL_LOAD, LOAD_LOCK, ensure_backend_local_load, get_global_loop, enqueue_task, remove_task
from app.services.history_service import save_to_history
from app.utils.backend import get_best_backend, get_comfy_history
from app.utils.images import convert_output_to_jpg, download_image
from app.ws.manager import manager


router = APIRouter()


@router.post("/api/generate")
def generate(req: GenerateRequest):
    current_task = enqueue_task(req.client_id)
    target_backend = None

    try:
        ensure_backend_local_load()
        required_images = []
        for node_id, node_inputs in req.params.items():
            if isinstance(node_inputs, dict) and "image" in node_inputs:
                image_name = node_inputs["image"]
                if isinstance(image_name, str) and image_name:
                    required_images.append(image_name)

        target_backend = get_best_backend(required_images, BACKEND_LOCAL_LOAD, LOAD_LOCK)
        with LOAD_LOCK:
            BACKEND_LOCAL_LOAD[target_backend] += 1

        for image_name in required_images:
            need_sync = False
            try:
                check_url = f"http://{target_backend}/view?filename={urllib.parse.quote(image_name)}&type=input"
                response = requests.get(check_url, stream=True, timeout=0.5)
                response.close()
                if response.status_code != 200:
                    need_sync = True
            except Exception:
                need_sync = True

            if need_sync:
                image_content = None
                image_type = "image/png"
                for addr in get_comfyui_instances():
                    if addr == target_backend:
                        continue
                    try:
                        src_url = f"http://{addr}/view?filename={urllib.parse.quote(image_name)}&type=input"
                        response = requests.get(src_url, timeout=5)
                        if response.status_code == 200:
                            image_content = response.content
                            image_type = response.headers.get("Content-Type", "image/png")
                            break
                    except Exception:
                        continue

                if image_content:
                    try:
                        files = {"image": (image_name, image_content, image_type)}
                        requests.post(f"http://{target_backend}/upload/image", files=files, timeout=10)
                    except Exception as exc:
                        print(f"Sync upload failed: {exc}")

        workflow_name = req.workflow_json or get_workflow_zimage()
        workflow_path = os.path.join(WORKFLOW_DIR, workflow_name)
        if not os.path.exists(workflow_path) and workflow_name == get_workflow_zimage():
            workflow_path = get_workflow_path()
        if not os.path.exists(workflow_path):
            raise Exception(f"Workflow file not found: {workflow_name}")

        with open(workflow_path, "r", encoding="utf-8") as file:
            workflow = json.load(file)

        seed = random.randint(1, 10**15)

        # 根据 class_type 自动注入画布参数，不再硬编码节点 ID
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

        for node_id, node_inputs in req.params.items():
            if node_id in workflow:
                if "inputs" not in workflow[node_id]:
                    workflow[node_id]["inputs"] = {}
                for input_name, value in node_inputs.items():
                    workflow[node_id]["inputs"][input_name] = value

        payload = {"prompt": workflow, "client_id": req.client_id}
        data = json.dumps(payload).encode("utf-8")
        try:
            post_req = urllib.request.Request(f"http://{target_backend}/prompt", data=data)
            prompt_id = json.loads(urllib.request.urlopen(post_req, timeout=10).read())["prompt_id"]
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise Exception(f"HTTP Error {exc.code}: {error_body}")

        history_data = None
        for _ in range(300):
            try:
                response = get_comfy_history(target_backend, prompt_id)
                if prompt_id in response:
                    history_data = response[prompt_id]
                    break
            except Exception:
                pass
            time.sleep(1)

        if not history_data:
            raise Exception("ComfyUI 渲染超时")

        local_urls = []
        current_timestamp = time.time()
        if "outputs" in history_data:
            for node_id in history_data["outputs"]:
                node_output = history_data["outputs"][node_id]
                if "images" in node_output:
                    for image in node_output["images"]:
                        comfy_url_path = f"/view?filename={image['filename']}&subfolder={image['subfolder']}&type={image['type']}"
                        prefix = f"{req.type}_{int(current_timestamp)}_"
                        local_path = download_image(target_backend, comfy_url_path, prefix=prefix)
                        if req.convert_to_jpg:
                            local_path = convert_output_to_jpg(local_path)
                        local_urls.append(local_path)

        result = {
            "prompt": req.prompt if req.prompt else "Detail Enhance",
            "images": local_urls,
            "seed": seed,
            "timestamp": current_timestamp,
            "type": req.type,
            "params": req.params,
        }
        save_to_history(result)
        loop = get_global_loop()
        if loop:
            asyncio.run_coroutine_threadsafe(manager.broadcast_new_image(result), loop)
        return result
    except Exception as exc:
        return {"images": [], "error": str(exc)}
    finally:
        if target_backend:
            with LOAD_LOCK:
                if BACKEND_LOCAL_LOAD.get(target_backend, 0) > 0:
                    BACKEND_LOCAL_LOAD[target_backend] -= 1
        remove_task(current_task)
