from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.models.responses import UploadResponse
from app.services.file_storage import to_data_url

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    settings = get_settings()

    if not file.content_type:
        raise HTTPException(status_code=400, detail="File content type is missing")

    if not file.content_type.startswith(("image/", "video/")):
        raise HTTPException(
            status_code=400, detail="Only image/video uploads are supported"
        )

    data = await file.read()
    size_mb = len(data) / (1024 * 1024)

    if size_mb > settings.upload_max_mb:
        raise HTTPException(
            status_code=400, detail=f"File exceeds {settings.upload_max_mb}MB"
        )

    data_url = to_data_url(data, file.content_type)
    return UploadResponse(
        success=True,
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        size=len(data),
        data_url=data_url,
    )
