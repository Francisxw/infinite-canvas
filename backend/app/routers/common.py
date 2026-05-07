from __future__ import annotations

from fastapi.responses import JSONResponse


def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    extra: dict[str, object] | None = None,
) -> JSONResponse:
    content: dict[str, object] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if extra:
        content.update(extra)
    return JSONResponse(status_code=status_code, content=content)
