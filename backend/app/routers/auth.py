from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.models.requests import (
    UpdateAccountSettingsRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.rate_limit import limiter
from app.routers.common import (
    bearer_scheme,
    clear_session_cookie,
    error_response,
    require_user,
    resolve_session_token,
    set_session_cookie,
)
from app.services.account_store import (
    AccountStoreError,
    PublicUserRecord,
    account_store,
)

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/register")
@limiter.limit("30/minute")
async def register(request: Request, payload: UserRegisterRequest):
    try:
        result = account_store.register(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
        response = JSONResponse(content=result)
        set_session_cookie(response, str(result["token"]))
        return response
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)


@router.post("/auth/login")
@limiter.limit("30/minute")
async def login(request: Request, payload: UserLoginRequest):
    try:
        result = account_store.login(email=payload.email, password=payload.password)
        response = JSONResponse(content=result)
        set_session_cookie(response, str(result["token"]))
        return response
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)


@router.post("/auth/logout")
@limiter.limit("60/minute")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    token = resolve_session_token(request, credentials)
    if token:
        account_store.logout(token)
    response = JSONResponse(content={"success": True})
    clear_session_cookie(response)
    return response


@router.get("/account/profile")
@limiter.limit("120/minute")
async def profile(
    request: Request, current_user: PublicUserRecord = Depends(require_user)
):
    try:
        return account_store.get_profile(str(current_user["id"]))
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)


@router.get("/account/packages")
@limiter.limit("120/minute")
async def list_packages(
    request: Request, current_user: PublicUserRecord = Depends(require_user)
):
    return {"packages": account_store.list_packages(), "user": current_user}


@router.get("/account/settings")
@limiter.limit("120/minute")
async def get_account_settings(
    request: Request,
    current_user: PublicUserRecord = Depends(require_user),
):
    try:
        return account_store.get_account_settings(str(current_user["id"]))
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)


@router.patch("/account/settings")
@limiter.limit("60/minute")
async def update_account_settings(
    request: Request,
    payload: UpdateAccountSettingsRequest,
    current_user: PublicUserRecord = Depends(require_user),
):
    try:
        return account_store.update_account_settings(
            user_id=str(current_user["id"]),
            openrouter_mode=payload.openrouter_mode,
            openrouter_api_key=payload.openrouter_api_key,
            preferred_models=payload.preferred_models,
        )
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)


@router.post("/account/recharge")
@limiter.limit("30/minute")
async def recharge_deprecated(
    request: Request,
    current_user: PublicUserRecord = Depends(require_user),
):
    return error_response(
        410,
        "recharge_endpoint_deprecated",
        "Use /api/payments/wechat/orders to create a WeChat Pay recharge order.",
    )
