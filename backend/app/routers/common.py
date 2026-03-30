from __future__ import annotations

from fastapi import Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.services.account_store import (
    AccountStoreError,
    PublicUserRecord,
    account_store,
)


SESSION_COOKIE_NAME = "ic_session"
bearer_scheme = HTTPBearer(auto_error=False)


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


def resolve_session_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials

    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_token:
        return None

    normalized = cookie_token.strip()
    return normalized or None


def require_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> PublicUserRecord:
    token = resolve_session_token(request, credentials)
    if not token:
        raise AccountStoreError("auth_required", "Please sign in to continue.", 401)

    return account_store.resolve_token(token)


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    secure = settings.app_env == "production"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.account_session_ttl_hours * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    secure = settings.app_env == "production"
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
