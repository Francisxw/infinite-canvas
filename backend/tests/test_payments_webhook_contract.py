from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

import app.routers.payments as payments_router
from app.main import app
from app.services.account_store import account_store, AccountStoreError
from app.services.wechat_pay import WeChatPayError


client = TestClient(app)


@pytest.fixture(autouse=True)
def use_temp_account_store(tmp_path: Path):
    original_path = account_store._file_path
    account_store._file_path = tmp_path / "account-store.db"
    yield
    account_store._file_path = original_path


def create_authenticated_order(monkeypatch) -> tuple[dict[str, str], dict[str, object]]:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "notify-contract@example.com",
            "password": "secret123",
            "display_name": "Notify Contract",
        },
    )
    headers = {"Authorization": f"Bearer {register_response.json()['token']}"}

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "ensure_configured", lambda: None
    )

    async def fake_create_native_order(
        *,
        out_trade_no: str,
        description: str,
        total_fee_fen: int,
        attach: str | None = None,
    ):
        return {"code_url": "weixin://wxpay/contract-order"}

    monkeypatch.setattr(
        payments_router.wechat_pay_service,
        "create_native_order",
        fake_create_native_order,
    )

    create_response = client.post(
        "/api/payments/wechat/orders",
        headers=headers,
        json={"package_id": "starter"},
    )
    assert create_response.status_code == 200
    return headers, create_response.json()["order"]


def test_wechat_notify_returns_204_on_success(monkeypatch) -> None:
    _, created_order = create_authenticated_order(monkeypatch)

    async def fake_parse_callback(*, headers: dict[str, str], body: bytes):
        return {
            "resource": {
                "out_trade_no": created_order["out_trade_no"],
                "trade_state": "SUCCESS",
                "transaction_id": "wx_txn_notify_contract_001",
            }
        }

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "parse_callback", fake_parse_callback
    )

    notify_response = client.post("/api/payments/wechat/notify", json={})

    assert notify_response.status_code == 204
    assert notify_response.content == b""


def test_wechat_notify_returns_204_for_duplicate_notifications(monkeypatch) -> None:
    _, created_order = create_authenticated_order(monkeypatch)

    async def fake_parse_callback(*, headers: dict[str, str], body: bytes):
        return {
            "resource": {
                "out_trade_no": created_order["out_trade_no"],
                "trade_state": "SUCCESS",
                "transaction_id": "wx_txn_notify_contract_002",
            }
        }

    def fake_mark_paid(
        *, out_trade_no: str, payment_reference: str, provider_payload=None
    ):
        raise AccountStoreError(
            "duplicate_payment_reference",
            "This payment reference has already been processed.",
            409,
        )

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "parse_callback", fake_parse_callback
    )
    monkeypatch.setattr(
        payments_router.account_store, "mark_recharge_order_paid", fake_mark_paid
    )

    notify_response = client.post("/api/payments/wechat/notify", json={})

    assert notify_response.status_code == 204
    assert notify_response.content == b""


def test_wechat_notify_returns_failure_response_for_missing_order(monkeypatch) -> None:
    async def fake_parse_callback(*, headers: dict[str, str], body: bytes):
        return {
            "resource": {
                "out_trade_no": "ICMISSINGORDER001",
                "trade_state": "SUCCESS",
                "transaction_id": "wx_txn_missing_order_001",
            }
        }

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "parse_callback", fake_parse_callback
    )

    notify_response = client.post("/api/payments/wechat/notify", json={})

    assert notify_response.status_code == 500
    assert notify_response.json() == {
        "error": {
            "code": "ORDER_NOT_FOUND",
            "message": "Recharge order not found.",
        }
    }


def test_wechat_notify_returns_failure_response_for_invalid_callback(
    monkeypatch,
) -> None:
    async def fake_parse_callback(*, headers: dict[str, str], body: bytes):
        raise WeChatPayError(
            "wechatpay_callback_invalid",
            "Invalid WeChat Pay callback payload.",
            400,
        )

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "parse_callback", fake_parse_callback
    )

    notify_response = client.post("/api/payments/wechat/notify", json={})

    assert notify_response.status_code == 400
    assert notify_response.json() == {
        "error": {
            "code": "INVALID_CALLBACK",
            "message": "Invalid WeChat Pay callback payload.",
        }
    }


def test_wechat_create_failure_keeps_order_pending_for_later_success(
    monkeypatch,
) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "notify-late-success@example.com",
            "password": "secret123",
            "display_name": "Notify Late Success",
        },
    )
    headers = {"Authorization": f"Bearer {register_response.json()['token']}"}

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "ensure_configured", lambda: None
    )
    user = register_response.json()["user"]
    original_create_recharge_order = payments_router.account_store.create_recharge_order
    captured_created: dict[str, Any] = {}

    def capture_create_recharge_order(*, user_id: str, package_id: str, provider: str):
        created = cast(
            dict[str, Any],
            original_create_recharge_order(
                user_id=user_id,
                package_id=package_id,
                provider=provider,
            ),
        )
        captured_created.update(created)
        return created

    monkeypatch.setattr(
        payments_router.account_store,
        "create_recharge_order",
        capture_create_recharge_order,
    )

    async def failing_create_native_order(
        *,
        out_trade_no: str,
        description: str,
        total_fee_fen: int,
        attach: str | None = None,
    ):
        raise WeChatPayError(
            "wechatpay_create_failed",
            "Failed to create WeChat Pay order.",
            502,
        )

    monkeypatch.setattr(
        payments_router.wechat_pay_service,
        "create_native_order",
        failing_create_native_order,
    )

    failed_create_response = client.post(
        "/api/payments/wechat/orders",
        headers=headers,
        json={"package_id": "starter"},
    )
    created_order = cast(dict[str, Any], captured_created["order"])
    assert failed_create_response.status_code == 202
    assert failed_create_response.json()["warning"]["code"] == "wechatpay_create_failed"
    assert failed_create_response.json()["order"]["id"] == created_order["id"]
    assert "order" in captured_created

    order_payload = cast(
        dict[str, Any],
        payments_router.account_store.get_recharge_order(
            user_id=str(user["id"]),
            order_id=str(created_order["id"]),
        ),
    )
    assert order_payload["order"]["status"] == "pending"

    async def fake_parse_callback(*, headers: dict[str, str], body: bytes):
        return {
            "resource": {
                "out_trade_no": created_order["out_trade_no"],
                "trade_state": "SUCCESS",
                "transaction_id": "wx_txn_late_success_001",
            }
        }

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "parse_callback", fake_parse_callback
    )

    notify_response = client.post("/api/payments/wechat/notify", json={})
    assert notify_response.status_code == 204

    profile_response = client.get("/api/account/profile", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["user"]["points"] == 340


def test_wechat_notify_wraps_unexpected_callback_exceptions(monkeypatch) -> None:
    async def fake_parse_callback(*, headers: dict[str, str], body: bytes):
        raise RuntimeError("socket closed")

    monkeypatch.setattr(
        payments_router.wechat_pay_service, "parse_callback", fake_parse_callback
    )

    notify_response = client.post("/api/payments/wechat/notify", json={})

    assert notify_response.status_code == 500
    assert notify_response.json() == {
        "error": {
            "code": "SYSTEM_ERROR",
            "message": "Unexpected WeChat Pay callback error.",
        }
    }
