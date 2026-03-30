from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse

from app.rate_limit import limiter
from app.config import get_settings
from app.models.responses import UploadResponse
from app.routers.common import error_response, require_user
from app.services.account_store import PublicUserRecord
from app.services.file_storage import (
    file_extension_allowed,
    media_kind_matches_content_type,
    to_data_url,
)

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("60/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: PublicUserRecord = Depends(require_user),
) -> UploadResponse | JSONResponse:
    settings = get_settings()

    if not file.content_type:
        return error_response(
            400, "upload_content_type_missing", "File content type is missing"
        )

    if not file.content_type.startswith(("image/", "video/")):
        return error_response(
            400,
            "upload_media_type_unsupported",
            "Only image/video uploads are supported",
        )

    if not file_extension_allowed(file.filename):
        return error_response(
            400,
            "upload_extension_unsupported",
            "Unsupported file extension.",
        )

    content_length_header = request.headers.get("content-length")
    if content_length_header:
        try:
            content_length = int(content_length_header)
        except ValueError:
            content_length = None
        else:
            if content_length > settings.upload_max_mb * 1024 * 1024:
                return error_response(
                    400,
                    "upload_too_large",
                    f"File exceeds {settings.upload_max_mb}MB",
                )

    data = await file.read()
    size_mb = len(data) / (1024 * 1024)

    if size_mb > settings.upload_max_mb:
        return error_response(
            400,
            "upload_too_large",
            f"File exceeds {settings.upload_max_mb}MB",
        )

    if not media_kind_matches_content_type(data, file.content_type):
        return error_response(
            400,
            "upload_signature_invalid",
            "Uploaded file content does not match the declared media type.",
        )

    data_url = to_data_url(data, file.content_type)
    return UploadResponse(
        success=True,
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        size=len(data),
        data_url=data_url,
    )
