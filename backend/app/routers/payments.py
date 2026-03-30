from __future__ import annotations

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response

from app.models.requests import CreateWeChatRechargeOrderRequest
from app.rate_limit import limiter
from app.routers.common import error_response, require_user
from app.services.account_store import AccountStoreError, account_store
from app.services.wechat_pay import WeChatPayError, wechat_pay_service

router = APIRouter(prefix="/api/payments", tags=["payments"])
logger = logging.getLogger(__name__)


def callback_success_response() -> Response:
    return Response(status_code=204)


def callback_failure_response(
    status_code: int, code: str, message: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


def recovery_response(
    *,
    order: dict[str, Any],
    package: dict[str, Any],
    user: dict[str, Any],
    warning_code: str,
    warning_message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=202,
        content={
            "order": order,
            "package": package,
            "user": user,
            "payment": None,
            "warning": {
                "code": warning_code,
                "message": warning_message,
            },
        },
    )


@router.post("/wechat/orders")
@limiter.limit("30/minute")
async def create_wechat_order(
    request: Request,
    payload: CreateWeChatRechargeOrderRequest,
    current_user: dict[str, str | int] = Depends(require_user),
):
    created: dict[str, Any] | None = None
    try:
        wechat_pay_service.ensure_configured()
        created = cast(
            dict[str, Any],
            account_store.create_recharge_order(
                user_id=str(current_user["id"]),
                package_id=payload.package_id,
                provider="wechatpay_native",
            ),
        )
        order = cast(dict[str, Any], created["order"])
        package = cast(dict[str, Any], created["package"])
        payment_payload = await wechat_pay_service.create_native_order(
            out_trade_no=str(order["out_trade_no"]),
            description=f"Infinite Studio {package['label']} recharge",
            total_fee_fen=int(package["price_cny"]) * 100,
            attach=str(current_user["id"]),
        )
        updated_order = account_store.set_recharge_order_code_url(
            order_id=str(order["id"]),
            code_url=str(payment_payload["code_url"]),
            provider_payload=payment_payload,
        )
        return {
            "order": updated_order,
            "package": package,
            "user": created["user"],
            "payment": {
                "provider": "wechatpay_native",
                "code_url": payment_payload["code_url"],
                "display_mode": "qr",
            },
        }
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except WeChatPayError as exc:
        if created:
            logger.warning("wechat create order pending recovery: %s", exc.code)
            return recovery_response(
                order=cast(dict[str, Any], created["order"]),
                package=cast(dict[str, Any], created["package"]),
                user=cast(dict[str, Any], created["user"]),
                warning_code=exc.code,
                warning_message=(
                    "WeChat Pay order was created, but the QR code is not ready yet. Please keep this order open and refresh its status shortly."
                ),
            )
        return error_response(exc.status_code, exc.code, exc.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected WeChat Pay order creation failure")
        if created:
            return recovery_response(
                order=cast(dict[str, Any], created["order"]),
                package=cast(dict[str, Any], created["package"]),
                user=cast(dict[str, Any], created["user"]),
                warning_code="wechatpay_order_pending_recovery",
                warning_message=(
                    "WeChat Pay order was created, but the QR code is not ready yet. Please keep this order open and refresh its status shortly."
                ),
            )
        return error_response(
            500, "wechatpay_create_failed", "Failed to create WeChat Pay order."
        )


@router.get("/wechat/orders/{order_id}")
@limiter.limit("60/minute")
async def get_wechat_order(
    request: Request,
    order_id: str,
    current_user: dict[str, str | int] = Depends(require_user),
):
    try:
        order_payload = cast(
            dict[str, Any],
            account_store.get_recharge_order(
                user_id=str(current_user["id"]),
                order_id=order_id,
            ),
        )
        order = cast(dict[str, Any], order_payload["order"])

        if order["status"] == "pending" and wechat_pay_service.is_configured():
            query_payload = await wechat_pay_service.query_order(
                out_trade_no=str(order["out_trade_no"]),
            )
            trade_state = query_payload.get("trade_state")
            if trade_state == "SUCCESS":
                payment_reference = query_payload.get("transaction_id") or str(
                    order["out_trade_no"]
                )
                return account_store.mark_recharge_order_paid(
                    out_trade_no=str(order["out_trade_no"]),
                    payment_reference=str(payment_reference),
                    provider_payload=query_payload,
                )
            if trade_state in {"CLOSED", "REVOKED"}:
                updated = account_store.update_recharge_order_status(
                    order_id=str(order["id"]),
                    status="expired",
                    provider_payload=query_payload,
                )
                return {**order_payload, "order": updated}
            if trade_state in {"PAYERROR"}:
                updated = account_store.update_recharge_order_status(
                    order_id=str(order["id"]),
                    status="failed",
                    provider_payload=query_payload,
                )
                return {**order_payload, "order": updated}

        return order_payload
    except AccountStoreError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except WeChatPayError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected WeChat Pay order query failure")
        return error_response(
            500, "wechatpay_query_failed", "Failed to query WeChat Pay order."
        )


@router.post("/wechat/notify")
async def wechat_notify(request: Request):
    try:
        payload = await wechat_pay_service.parse_callback(
            headers=dict(request.headers),
            body=await request.body(),
        )
        resource_value = payload.get("resource")
        resource: dict[str, Any] = (
            cast(dict[str, Any], resource_value)
            if isinstance(resource_value, dict)
            else payload
        )
        out_trade_no = resource.get("out_trade_no")
        trade_state = resource.get("trade_state")
        transaction_id = resource.get("transaction_id") or out_trade_no

        if out_trade_no and trade_state == "SUCCESS":
            account_store.mark_recharge_order_paid(
                out_trade_no=str(out_trade_no),
                payment_reference=str(transaction_id),
                provider_payload=payload,
            )
            return callback_success_response()

        if out_trade_no and trade_state in {"CLOSED", "REVOKED"}:
            order = account_store.get_recharge_order_by_trade_no(str(out_trade_no))
            if order:
                account_store.update_recharge_order_status(
                    order_id=str(order["id"]),
                    status="expired",
                    provider_payload=payload,
                )

        return callback_success_response()
    except AccountStoreError as exc:
        if exc.code in {
            "duplicate_payment_reference",
            "order_state_invalid",
        }:
            return callback_success_response()
        if exc.code == "order_not_found":
            return callback_failure_response(500, "ORDER_NOT_FOUND", exc.message)
        return callback_failure_response(500, "SYSTEM_ERROR", exc.message)
    except WeChatPayError as exc:
        code = "INVALID_CALLBACK" if exc.status_code < 500 else "SYSTEM_ERROR"
        return callback_failure_response(exc.status_code, code, exc.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected WeChat Pay callback error")
        return callback_failure_response(
            500, "SYSTEM_ERROR", "Unexpected WeChat Pay callback error."
        )
