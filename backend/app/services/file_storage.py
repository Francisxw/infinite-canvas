import base64
from pathlib import Path


ALLOWED_MEDIA_EXTENSIONS = {
    ".gif",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp4",
    ".png",
    ".webm",
    ".webp",
}


def file_extension_allowed(filename: str | None) -> bool:
    if not filename:
        return False
    return Path(filename).suffix.lower() in ALLOWED_MEDIA_EXTENSIONS


def detect_media_kind(content: bytes) -> str | None:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image"
    if content.startswith(b"\xff\xd8\xff"):
        return "image"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "image"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image"
    if len(content) >= 12 and content[4:8] == b"ftyp":
        return "video"
    if content.startswith(b"\x1a\x45\xdf\xa3"):
        return "video"
    if content.startswith(b"OggS"):
        return "video"
    return None


def media_kind_matches_content_type(content: bytes, content_type: str) -> bool:
    detected_kind = detect_media_kind(content)
    if not detected_kind:
        return False
    return content_type.startswith(f"{detected_kind}/")


def to_data_url(content: bytes, content_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"
