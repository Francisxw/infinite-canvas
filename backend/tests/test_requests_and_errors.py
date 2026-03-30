from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

import app.routers.openrouter as openrouter_router
import app.routers.payments as payments_router
from app.main import app
from app.models.requests import TextGenerationRequest, VideoGenerationRequest
from app.services.account_store import account_store
from app.services.providers.base import ProviderUpstreamError


client = TestClient(app)


@pytest.fixture(autouse=True)
def use_temp_account_store(tmp_path: Path):
    original_path = account_store._file_path
    account_store._file_path = tmp_path / "account-store.db"
    yield
    account_store._file_path = original_path


def auth_headers() -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "tester@example.com",
            "password": "secret123",
            "display_name": "Tester",
        },
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_text_generation_request_accepts_structured_prompt_parts() -> None:
    request = TextGenerationRequest.model_validate(
        {
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": [
                {"type": "text", "text": "describe this image"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.png",
                        "detail": "auto",
                    },
                },
            ],
        }
    )

    assert len(request.prompt) == 2


def test_text_generation_request_rejects_unknown_prompt_part_shape() -> None:
    try:
        TextGenerationRequest.model_validate(
            {
                "provider": "openrouter",
                "model": "google/gemini-2.5-flash",
                "prompt": [{"type": "broken", "value": "oops"}],
            }
        )
    except ValidationError as exc:
        assert "type" in str(exc)
    else:
        raise AssertionError("ValidationError was expected for invalid prompt part")


def test_generate_text_returns_safe_error_payload(monkeypatch) -> None:
    class FailingProvider:
        async def generate_text(self, payload):
            raise ProviderUpstreamError(
                "openrouter",
                code="http_error",
                message="The upstream provider request failed.",
            )

        async def generate_image(self, payload):
            raise NotImplementedError

        async def get_models(self, output_modality="image"):
            raise NotImplementedError

    monkeypatch.setattr(
        openrouter_router,
        "get_provider",
        lambda provider, user_id=None: FailingProvider(),
    )

    response = client.post(
        "/api/generate-text",
        headers=auth_headers(),
        json={
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": "hello",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "openrouter_http_error",
            "message": "The upstream provider request failed.",
        }
    }


def test_video_generation_request_accepts_speed() -> None:
    request = VideoGenerationRequest.model_validate(
        {
            "provider": "openrouter",
            "model": "google/veo-3.1",
            "prompt": "slow motion fabric in the wind",
            "aspect_ratio": "16:9",
            "duration": "5s",
            "quality": "1080p",
            "speed": "fast",
        }
    )

    assert request.speed == "fast"


def test_generate_video_returns_safe_error_payload(monkeypatch) -> None:
    class FailingProvider:
        async def generate_text(self, payload):
            raise NotImplementedError

        async def generate_image(self, payload):
            raise NotImplementedError

        async def generate_video(self, payload):
            raise ProviderUpstreamError(
                "openrouter",
                code="video_generation_unsupported",
                message="Video generation is temporarily unavailable.",
            )

        async def get_models(self, output_modality="image"):
            raise NotImplementedError

    monkeypatch.setattr(
        openrouter_router,
        "get_provider",
        lambda provider, user_id=None: FailingProvider(),
    )

    response = client.post(
        "/api/generate-video",
        headers=auth_headers(),
        json={
            "provider": "openrouter",
            "model": "google/veo-3.1",
            "prompt": "paper sculpture unfolding",
            "aspect_ratio": "16:9",
            "duration": "5s",
            "quality": "1080p",
            "speed": "standard",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "openrouter_video_generation_unsupported",
            "message": "Video generation is temporarily unavailable.",
        }
    }


def test_legacy_direct_recharge_endpoint_is_deprecated() -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "credits@example.com",
            "password": "secret123",
            "display_name": "Credits User",
        },
    )

    payload = register_response.json()
    headers = {"Authorization": f"Bearer {payload['token']}"}
    recharge_response = client.post(
        "/api/account/recharge",
        headers=headers,
    )
    assert recharge_response.status_code == 410
    assert recharge_response.json() == {
        "error": {
            "code": "recharge_endpoint_deprecated",
            "message": "Use /api/payments/wechat/orders to create a WeChat Pay recharge order.",
        }
    }


def test_legacy_direct_recharge_duplicate_path_is_unavailable() -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "dup@example.com",
            "password": "secret123",
            "display_name": "Dup User",
        },
    )

    headers = {"Authorization": f"Bearer {register_response.json()['token']}"}
    response = client.post(
        "/api/account/recharge",
        headers=headers,
    )

    assert response.status_code == 410
    assert response.json() == {
        "error": {
            "code": "recharge_endpoint_deprecated",
            "message": "Use /api/payments/wechat/orders to create a WeChat Pay recharge order.",
        }
    }


def test_legacy_json_data_migrates_and_upgrades_password_hash() -> None:
    legacy_path = account_store._file_path.with_suffix(".json")
    legacy_path.write_text(
        """{
  "users": [
    {
      "id": "user_legacy",
      "email": "legacy@example.com",
      "display_name": "Legacy User",
      "password_hash": "0f873a0c88139de04b694ceb6416a059b2b91e4b014633ca0f78c18ef2a053b3",
      "password_salt": "salt1234",
      "points": 120,
      "created_at": "2026-03-25T00:00:00+00:00",
      "ledger": [
        {
          "id": "ledger_legacy_bonus",
          "type": "signup_bonus",
          "amount": 120,
          "balance_after": 120,
          "description": "Registration bonus credited.",
          "created_at": "2026-03-25T00:00:00+00:00"
        }
      ]
    }
  ],
  "sessions": [],
  "recharges": []
}""",
        encoding="utf-8",
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "legacy@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["user"]["email"] == "legacy@example.com"

    migrated_user = account_store.get_full_user("user_legacy")
    assert migrated_user["password_scheme"] == "pbkdf2_sha256"
    assert migrated_user["password_salt"] is None


def test_legacy_json_migration_runs_when_database_already_has_users() -> None:
    existing_user = client.post(
        "/api/auth/register",
        json={
            "email": "existing@example.com",
            "password": "secret123",
            "display_name": "Existing User",
        },
    )
    assert existing_user.status_code == 200

    legacy_path = account_store._file_path.with_suffix(".json")
    legacy_path.write_text(
        """{
  "users": [
    {
      "id": "user_late_legacy",
      "email": "late-legacy@example.com",
      "display_name": "Late Legacy",
      "password_hash": "0f873a0c88139de04b694ceb6416a059b2b91e4b014633ca0f78c18ef2a053b3",
      "password_salt": "salt1234",
      "points": 80,
      "created_at": "2026-03-25T00:00:00+00:00",
      "ledger": []
    }
  ],
  "sessions": [],
  "recharges": []
}""",
        encoding="utf-8",
    )

    login_response = client.post(
        "/api/auth/login",
        json={"email": "late-legacy@example.com", "password": "password123"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == "late-legacy@example.com"


def test_invalid_legacy_hash_fails_as_auth_error() -> None:
    legacy_path = account_store._file_path.with_suffix(".json")
    legacy_path.write_text(
        """{
  "users": [
    {
      "id": "user_invalid_legacy",
      "email": "invalid-legacy@example.com",
      "display_name": "Invalid Legacy",
      "password_hash": "not-a-passlib-hash",
      "password_salt": null,
      "points": 50,
      "created_at": "2026-03-25T00:00:00+00:00",
      "ledger": []
    }
  ],
  "sessions": [],
  "recharges": []
}""",
        encoding="utf-8",
    )

    login_response = client.post(
        "/api/auth/login",
        json={"email": "invalid-legacy@example.com", "password": "password123"},
    )

    assert login_response.status_code == 401
    assert login_response.json() == {
        "error": {
            "code": "invalid_credentials",
            "message": "Invalid email or password.",
        }
    }


def test_expired_session_is_rejected() -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "expired@example.com",
            "password": "secret123",
            "display_name": "Expired User",
        },
    )
    token = register_response.json()["token"]

    connection = sqlite3.connect(account_store._file_path)
    try:
        connection.execute(
            "UPDATE sessions SET expires_at = ? WHERE token = ?",
            ("2000-01-01T00:00:00+00:00", token),
        )
        connection.commit()
    finally:
        connection.close()

    response = client.get(
        "/api/account/profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "auth_required",
            "message": "Please sign in to continue.",
        }
    }


def test_generate_requires_auth() -> None:
    response = client.post(
        "/api/generate-text",
        json={
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": "hello",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "auth_required",
            "message": "Please sign in to continue.",
        }
    }


def test_wechat_order_requires_configuration() -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "wechat-missing@example.com",
            "password": "secret123",
            "display_name": "WeChat Missing",
        },
    )

    response = client.post(
        "/api/payments/wechat/orders",
        headers={"Authorization": f"Bearer {register_response.json()['token']}"},
        json={"package_id": "starter"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "payment_not_configured"


def test_wechat_order_create_and_query_success(monkeypatch) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "wechat@example.com",
            "password": "secret123",
            "display_name": "WeChat User",
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
        assert out_trade_no
        assert description
        assert total_fee_fen == 2900
        return {"code_url": "weixin://wxpay/mock-order"}

    async def fake_query_order(*, out_trade_no: str):
        return {
            "out_trade_no": out_trade_no,
            "trade_state": "SUCCESS",
            "transaction_id": "wx_txn_mock_001",
        }

    monkeypatch.setattr(
        payments_router.wechat_pay_service,
        "create_native_order",
        fake_create_native_order,
    )
    monkeypatch.setattr(
        payments_router.wechat_pay_service, "query_order", fake_query_order
    )
    monkeypatch.setattr(
        payments_router.wechat_pay_service, "is_configured", lambda: True
    )

    create_response = client.post(
        "/api/payments/wechat/orders",
        headers=headers,
        json={"package_id": "starter"},
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["payment"]["code_url"] == "weixin://wxpay/mock-order"
    assert created["order"]["status"] == "pending"

    query_response = client.get(
        f"/api/payments/wechat/orders/{created['order']['id']}",
        headers=headers,
    )

    assert query_response.status_code == 200
    queried = query_response.json()
    assert queried["order"]["status"] == "paid"
    assert queried["user"]["points"] == 340


def test_wechat_notify_marks_order_paid(monkeypatch) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "wechat-notify@example.com",
            "password": "secret123",
            "display_name": "WeChat Notify",
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
        return {"code_url": "weixin://wxpay/mock-notify"}

    async def fake_parse_callback(*, headers: dict[str, str], body: bytes):
        return {
            "resource": {
                "out_trade_no": created_order["out_trade_no"],
                "trade_state": "SUCCESS",
                "transaction_id": "wx_txn_notify_001",
            }
        }

    monkeypatch.setattr(
        payments_router.wechat_pay_service,
        "create_native_order",
        fake_create_native_order,
    )
    monkeypatch.setattr(
        payments_router.wechat_pay_service, "parse_callback", fake_parse_callback
    )

    create_response = client.post(
        "/api/payments/wechat/orders",
        headers=headers,
        json={"package_id": "starter"},
    )
    assert create_response.status_code == 200
    created_order = create_response.json()["order"]

    notify_response = client.post("/api/payments/wechat/notify", json={})
    assert notify_response.status_code == 204
    assert notify_response.content == b""

    profile_response = client.get("/api/account/profile", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["user"]["points"] == 340


def test_wechat_order_create_wraps_unexpected_provider_errors(monkeypatch) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "wechat-raw-create@example.com",
            "password": "secret123",
            "display_name": "WeChat Raw Create",
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
        raise RuntimeError("provider offline")

    monkeypatch.setattr(
        payments_router.wechat_pay_service,
        "create_native_order",
        fake_create_native_order,
    )

    response = client.post(
        "/api/payments/wechat/orders",
        headers=headers,
        json={"package_id": "starter"},
    )

    assert response.status_code == 202
    assert response.json()["warning"] == {
        "code": "wechatpay_order_pending_recovery",
        "message": "WeChat Pay order was created, but the QR code is not ready yet. Please keep this order open and refresh its status shortly.",
    }
    assert response.json()["order"]["status"] == "pending"


def test_wechat_order_query_wraps_unexpected_provider_errors(monkeypatch) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "wechat-raw-query@example.com",
            "password": "secret123",
            "display_name": "WeChat Raw Query",
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
        return {"code_url": "weixin://wxpay/raw-query"}

    async def fake_query_order(*, out_trade_no: str):
        raise RuntimeError("query transport failed")

    monkeypatch.setattr(
        payments_router.wechat_pay_service,
        "create_native_order",
        fake_create_native_order,
    )
    monkeypatch.setattr(
        payments_router.wechat_pay_service, "query_order", fake_query_order
    )
    monkeypatch.setattr(
        payments_router.wechat_pay_service, "is_configured", lambda: True
    )

    create_response = client.post(
        "/api/payments/wechat/orders",
        headers=headers,
        json={"package_id": "starter"},
    )
    order_id = create_response.json()["order"]["id"]

    response = client.get(
        f"/api/payments/wechat/orders/{order_id}",
        headers=headers,
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "wechatpay_query_failed",
            "message": "Failed to query WeChat Pay order.",
        }
    }


def test_generate_text_returns_post_deduction_balance_in_header(monkeypatch) -> None:
    class SuccessProvider:
        async def generate_text(self, payload):
            return {"text": "hello back"}

        async def generate_image(self, payload):
            raise NotImplementedError

        async def generate_video(self, payload):
            raise NotImplementedError

        async def get_models(self, output_modality="image"):
            raise NotImplementedError

    monkeypatch.setattr(
        openrouter_router,
        "get_provider",
        lambda provider, user_id=None: SuccessProvider(),
    )

    response = client.post(
        "/api/generate-text",
        headers=auth_headers(),
        json={
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": "hello",
        },
    )

    assert response.status_code == 200
    signup_bonus = 120
    text_cost = 25
    assert response.headers["X-Account-Points"] == str(signup_bonus - text_cost)


def test_generate_insufficient_points_returns_402(monkeypatch) -> None:
    class SuccessProvider:
        async def generate_text(self, payload):
            return {"text": "hello back"}

        async def generate_image(self, payload):
            raise NotImplementedError

        async def generate_video(self, payload):
            raise NotImplementedError

        async def get_models(self, output_modality="image"):
            raise NotImplementedError

    monkeypatch.setattr(
        openrouter_router,
        "get_provider",
        lambda provider, user_id=None: SuccessProvider(),
    )

    # Drain all points first by generating multiple texts (120 / 25 = 4 full)
    headers = auth_headers()
    for _ in range(4):
        resp = client.post(
            "/api/generate-text",
            headers=headers,
            json={
                "provider": "openrouter",
                "model": "google/gemini-2.5-flash",
                "prompt": "drain",
            },
        )
        assert resp.status_code == 200

    # 5th attempt should fail with 402
    response = client.post(
        "/api/generate-text",
        headers=headers,
        json={
            "provider": "openrouter",
            "model": "google/gemini-2.5-flash",
            "prompt": "one more",
        },
    )

    assert response.status_code == 402
    assert response.json()["error"]["code"] == "insufficient_points"
