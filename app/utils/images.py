import asyncio
import base64
import os
import shutil
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any

import httpx
from fastapi import HTTPException
from PIL import Image

from app.core.config import OUTPUT_DIR, get_ai_base_url, get_ai_request_timeout, get_image_poll_interval
from app.utils.providers import api_headers


def download_image(comfy_address: str, comfy_url_path: str, prefix: str = "studio_") -> str:
    filename = f"{prefix}{uuid.uuid4().hex[:10]}.png"
    local_path = os.path.join(OUTPUT_DIR, filename)
    full_url = f"http://{comfy_address}{comfy_url_path}"
    try:
        with urllib.request.urlopen(full_url) as response, open(local_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        return f"/output/{filename}"
    except Exception as exc:
        print(f"下载图片失败: {exc}")
        if comfy_url_path.startswith("/view"):
            return comfy_url_path.replace("/view", "/api/view", 1)
        return full_url


def output_file_from_url(url: str):
    if not url or not url.startswith("/output/"):
        return None
    filename = os.path.basename(urllib.parse.unquote(url.split("?", 1)[0]))
    path = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    output_root = os.path.abspath(OUTPUT_DIR)
    if os.path.commonpath([output_root, path]) != output_root or not os.path.exists(path):
        return None
    return path


def content_type_for_path(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "image/png"


def convert_output_to_jpg(url: str, quality: int = 88) -> str:
    path = output_file_from_url(url)
    if not path:
        return url
    root, ext = os.path.splitext(path)
    if ext.lower() in [".jpg", ".jpeg"]:
        return url
    jpg_path = f"{root}.jpg"
    try:
        with Image.open(path) as image:
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image.convert("RGBA"), mask=image.convert("RGBA").split()[-1])
                image = background
            else:
                image = image.convert("RGB")
            image.save(jpg_path, "JPEG", quality=quality, optimize=True)
        return f"/output/{os.path.basename(jpg_path)}"
    except Exception as exc:
        print(f"转换 JPG 失败: {exc}")
        return url


def reference_to_data_url(ref: dict[str, Any]) -> str:
    path = output_file_from_url(ref.get("url", ""))
    if not path:
        return ref.get("url", "")
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("ascii")
    return f"data:{content_type_for_path(path)};base64,{encoded}"


def extract_image(data: dict[str, Any]) -> dict[str, str]:
    if isinstance(data.get("data"), dict) and isinstance(data["data"].get("data"), dict):
        data = data["data"]["data"]
    images = data.get("data") or []
    if not images:
        raise HTTPException(status_code=502, detail="生图接口没有返回图片数据")
    first = images[0]
    if first.get("url"):
        return {"type": "url", "value": first["url"]}
    if first.get("b64_json"):
        return {"type": "b64", "value": first["b64_json"]}
    raise HTTPException(status_code=502, detail="无法识别生图接口返回格式")


def extract_task_id(data: dict[str, Any]) -> str | None:
    if data.get("task_id"):
        return str(data["task_id"])
    if data.get("id") and str(data.get("id", "")).startswith("task"):
        return str(data["id"])
    nested = data.get("data")
    if isinstance(nested, dict):
        return extract_task_id(nested)
    return None


async def wait_for_image_task(client: httpx.AsyncClient, task_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + get_ai_request_timeout()
    last_payload = {}
    while time.monotonic() < deadline:
        response = await client.get(f"{get_ai_base_url()}/v1/images/tasks/{task_id}", headers=api_headers())
        response.raise_for_status()
        last_payload = response.json()
        task_data = last_payload.get("data") if isinstance(last_payload.get("data"), dict) else last_payload
        status = str(task_data.get("status", "")).upper()
        if status == "SUCCESS":
            return last_payload
        if status == "FAILURE":
            reason = task_data.get("fail_reason") or last_payload.get("message") or "生图任务失败"
            raise HTTPException(status_code=502, detail=f"生图任务失败：{reason}")
        await asyncio.sleep(get_image_poll_interval())
    raise HTTPException(status_code=504, detail=f"生图任务超时，task_id={task_id}")


async def save_ai_image_to_output(image_data: dict[str, Any], prefix: str = "online_") -> str:
    filename = f"{prefix}{uuid.uuid4().hex[:10]}.png"
    path = os.path.join(OUTPUT_DIR, filename)
    if image_data["type"] == "b64":
        with open(path, "wb") as file:
            file.write(base64.b64decode(image_data["value"]))
        return f"/output/{filename}"
    value = image_data["value"]
    if value.startswith("/output/"):
        return value
    try:
        async with httpx.AsyncClient(timeout=get_ai_request_timeout()) as client:
            response = await client.get(value)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "jpeg" in content_type or "jpg" in content_type:
                filename = filename[:-4] + ".jpg"
                path = os.path.join(OUTPUT_DIR, filename)
            elif "webp" in content_type:
                filename = filename[:-4] + ".webp"
                path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "wb") as file:
                file.write(response.content)
            return f"/output/{filename}"
    except Exception as exc:
        print(f"保存上游图片失败: {exc}")
        return value


async def generate_ai_image(prompt: str, size: str, quality: str, model: str, reference_images: list[dict[str, Any]] | None = None):
    refs = [ref for ref in (reference_images or []) if ref.get("url")]
    async with httpx.AsyncClient(timeout=get_ai_request_timeout()) as client:
        if refs:
            files = []
            opened = []
            try:
                for ref in refs[:4]:
                    path = output_file_from_url(ref.get("url", ""))
                    if not path:
                        continue
                    file_handle = open(path, "rb")
                    opened.append(file_handle)
                    files.append(("image", (os.path.basename(path), file_handle, content_type_for_path(path))))
                data = {"model": model, "prompt": prompt, "size": size, "quality": quality, "response_format": "url", "n": "1"}
                response = await client.post(f"{get_ai_base_url()}/v1/images/edits", headers=api_headers(json_body=False), data=data, files=files)
            finally:
                for file_handle in opened:
                    file_handle.close()
        else:
            response = await client.post(
                f"{get_ai_base_url()}/v1/images/generations",
                headers=api_headers(),
                json={"model": model, "prompt": prompt, "size": size, "quality": quality, "response_format": "url", "n": 1},
            )
        response.raise_for_status()
        raw = response.json()
        try:
            return extract_image(raw), raw
        except HTTPException:
            task_id = extract_task_id(raw)
            if not task_id:
                raise
        task_result = await wait_for_image_task(client, task_id)
        return extract_image(task_result), task_result
