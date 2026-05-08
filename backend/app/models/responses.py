from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str


class UploadResponse(BaseModel):
    success: bool
    filename: str
    content_type: str
    size: int
    data_url: str
