from __future__ import annotations

import inspect
import importlib
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from app.config import get_settings


class WeChatPayError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class WeChatPayService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._async_wechat_pay: Any | None = None
        self._wechat_pay_type: Any | None = None

    def _required_fields(self) -> dict[str, str]:
        return {
            "WECHAT_PAY_MCHID": self._settings.wechat_pay_mchid,
            "WECHAT_PAY_APPID": self._settings.wechat_pay_appid,
            "WECHAT_PAY_PRIVATE_KEY": self._settings.wechat_pay_private_key,
            "WECHAT_PAY_CERT_SERIAL_NO": self._settings.wechat_pay_cert_serial_no,
            "WECHAT_PAY_APIV3_KEY": self._settings.wechat_pay_apiv3_key,
            "WECHAT_PAY_NOTIFY_URL": self._settings.wechat_pay_notify_url,
        }

    def is_configured(self) -> bool:
        notify_url = self._settings.wechat_pay_notify_url.strip()
        return all(
            value.strip() for value in self._required_fields().values()
        ) and notify_url.startswith("https://")

    def ensure_configured(self) -> None:
        missing = [
            name for name, value in self._required_fields().items() if not value.strip()
        ]
        if missing:
            raise WeChatPayError(
                "payment_not_configured",
                f"WeChat Pay is not configured. Missing: {', '.join(missing)}",
                503,
            )
        if not self._settings.wechat_pay_notify_url.strip().startswith("https://"):
            raise WeChatPayError(
                "payment_notify_url_invalid",
                "WECHAT_PAY_NOTIFY_URL must be an HTTPS callback URL.",
                503,
            )

    def _normalize_payload(self, payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                return {"raw": payload}
            if isinstance(parsed, dict):
                return parsed
        return {"raw": payload}

    def _load_sdk(self) -> tuple[Any, Any]:
        if self._async_wechat_pay is not None and self._wechat_pay_type is not None:
            return self._async_wechat_pay, self._wechat_pay_type

        try:
            async_module = importlib.import_module("wechatpayv3.async_")
            self._async_wechat_pay = getattr(async_module, "AsyncWeChatPay")
            self._wechat_pay_type = getattr(async_module, "WeChatPayType")
        except (ImportError, AttributeError) as exc:
            raise WeChatPayError(
                "payment_provider_unavailable",
                "WeChat Pay provider SDK is unavailable.",
                503,
            ) from exc

        return self._async_wechat_pay, self._wechat_pay_type

    def _wrap_unexpected_error(
        self, *, code: str, message: str, exc: Exception, status_code: int = 502
    ) -> WeChatPayError:
        if isinstance(exc, WeChatPayError):
            return exc

        return WeChatPayError(code, message, status_code)

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[Any]:
        self.ensure_configured()
        Path(self._settings.wechat_pay_cert_dir).mkdir(parents=True, exist_ok=True)

        AsyncWeChatPay, WeChatPayType = self._load_sdk()

        async with AsyncWeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=self._settings.wechat_pay_mchid,
            private_key=self._settings.wechat_pay_private_key,
            cert_serial_no=self._settings.wechat_pay_cert_serial_no,
            apiv3_key=self._settings.wechat_pay_apiv3_key,
            appid=self._settings.wechat_pay_appid,
            notify_url=self._settings.wechat_pay_notify_url,
            cert_dir=self._settings.wechat_pay_cert_dir,
        ) as client:
            yield client

    async def create_native_order(
        self,
        *,
        out_trade_no: str,
        description: str,
        total_fee_fen: int,
        attach: str | None = None,
    ) -> dict[str, Any]:
        try:
            _, WeChatPayType = self._load_sdk()

            async with self._client() as client:
                code, message = await client.pay(
                    description=description[:128],
                    out_trade_no=out_trade_no,
                    amount={"total": total_fee_fen, "currency": "CNY"},
                    attach=attach,
                    pay_type=WeChatPayType.NATIVE,
                )
        except Exception as exc:  # noqa: BLE001
            raise self._wrap_unexpected_error(
                code="wechatpay_create_failed",
                message="Failed to create WeChat Pay order.",
                exc=exc,
            ) from exc

        payload = self._normalize_payload(message)
        if code != 200 or not payload.get("code_url"):
            raise WeChatPayError(
                "wechatpay_create_failed",
                f"Failed to create WeChat Pay order: {payload.get('message') or payload.get('code') or code}",
                502,
            )
        return payload

    async def query_order(self, *, out_trade_no: str) -> dict[str, Any]:
        try:
            async with self._client() as client:
                code, message = await client.query(out_trade_no=out_trade_no)
        except Exception as exc:  # noqa: BLE001
            raise self._wrap_unexpected_error(
                code="wechatpay_query_failed",
                message="Failed to query WeChat Pay order.",
                exc=exc,
            ) from exc

        payload = self._normalize_payload(message)
        if code != 200:
            raise WeChatPayError(
                "wechatpay_query_failed",
                f"Failed to query WeChat Pay order: {payload.get('message') or payload.get('code') or code}",
                502,
            )
        return payload

    async def parse_callback(
        self, *, headers: dict[str, str], body: bytes
    ) -> dict[str, Any]:
        try:
            async with self._client() as client:
                result = client.callback(headers, body)
                if inspect.isawaitable(result):
                    result = await result
        except Exception as exc:  # noqa: BLE001
            raise self._wrap_unexpected_error(
                code="wechatpay_callback_invalid",
                message="Invalid WeChat Pay callback payload.",
                exc=exc,
                status_code=400,
            ) from exc

        if result is None:
            raise WeChatPayError(
                "wechatpay_callback_invalid",
                "Invalid WeChat Pay callback payload.",
                400,
            )

        payload = self._normalize_payload(result)
        if not payload:
            raise WeChatPayError(
                "wechatpay_callback_invalid",
                "Invalid WeChat Pay callback payload.",
                400,
            )
        return payload


wechat_pay_service = WeChatPayService()
