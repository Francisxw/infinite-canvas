from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime

from cryptography.fernet import Fernet, InvalidToken

from app.config import derive_account_secret_key, get_settings
from app.services.account_store.types import (
    OpenRouterSettingsRecord,
    PublicUserRecord,
    RechargeOrderRecord,
    RechargePackage,
    UserRecord,
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def hash_legacy_password(password: str, salt: str) -> str:
    digest = hashlib.sha256()
    digest.update(f"{salt}:{password}".encode("utf-8"))
    return digest.hexdigest()


def hash_session_token(token: str) -> str:
    digest = hashlib.sha256()
    digest.update(token.encode("utf-8"))
    return digest.hexdigest()


def _mask_secret(value: str) -> str:
    if len(value) <= 10:
        return "*" * len(value)
    return f"{value[:8]}...{value[-4:]}"


def row_to_public_user(row: sqlite3.Row) -> PublicUserRecord:
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "points": row["points"],
        "created_at": row["created_at"],
        "openrouter": _row_to_openrouter_settings(row),
    }


def _row_to_openrouter_settings(row: sqlite3.Row) -> OpenRouterSettingsRecord:
    encrypted_key = row["openrouter_api_key_encrypted"]
    mode = row["openrouter_mode"] or "platform"
    key_mask = None
    if encrypted_key:
        try:
            settings = get_settings()
            cipher = Fernet(derive_account_secret_key(settings.account_secret))
            decrypted = cipher.decrypt(str(encrypted_key).encode("utf-8")).decode(
                "utf-8"
            )
            key_mask = _mask_secret(decrypted)
        except (InvalidToken, ValueError, TypeError):
            key_mask = "已配置密钥"

    return {
        "mode": "custom" if mode == "custom" else "platform",
        "has_custom_key": bool(encrypted_key),
        "key_mask": key_mask,
        "preferred_models": {
            "text": None
            if row["openrouter_preferred_text_model"] is None
            else str(row["openrouter_preferred_text_model"]),
            "image": None
            if row["openrouter_preferred_image_model"] is None
            else str(row["openrouter_preferred_image_model"]),
            "video": None
            if row["openrouter_preferred_video_model"] is None
            else str(row["openrouter_preferred_video_model"]),
        },
    }


def package_payload(item: RechargePackage) -> dict[str, object]:
    return {
        "id": item.id,
        "label": item.label,
        "credits": item.credits,
        "bonus_credits": item.bonus_credits,
        "total_credits": item.total_credits,
        "price_cny": item.price_cny,
    }


def row_to_recharge_order(row: sqlite3.Row) -> RechargeOrderRecord:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "package_id": row["package_id"],
        "provider": row["provider"],
        "out_trade_no": row["out_trade_no"],
        "status": row["status"],
        "amount_cny": row["amount_cny"],
        "credits": row["credits"],
        "bonus_credits": row["bonus_credits"],
        "total_credits": row["total_credits"],
        "code_url": row["code_url"],
        "payment_reference": row["payment_reference"],
        "provider_payload": row["provider_payload"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "paid_at": row["paid_at"],
    }


def row_to_user_record(row: sqlite3.Row) -> UserRecord:
    """Convert a database row to a UserRecord with proper type coercion.

    This centralizes user record construction to eliminate duplication
    between get_full_user and get_user_by_token methods.
    """

    def str_or_none(field: str) -> str | None:
        value = row[field]
        return str(value) if value is not None else None

    def str_or_default(field: str, default: str = "") -> str:
        value = row[field]
        return str(value) if value is not None else default

    return {
        "id": str_or_default("id"),
        "email": str_or_default("email"),
        "display_name": str_or_default("display_name"),
        "password_hash": str_or_default("password_hash"),
        "password_salt": str_or_none("password_salt"),
        "password_scheme": str_or_default("password_scheme"),
        "points": int(row["points"]) if row["points"] is not None else 0,
        "created_at": str_or_default("created_at"),
        "openrouter_mode": str_or_default("openrouter_mode", "platform") or "platform",
        "openrouter_api_key_encrypted": str_or_none("openrouter_api_key_encrypted"),
        "openrouter_preferred_text_model": str_or_none(
            "openrouter_preferred_text_model"
        ),
        "openrouter_preferred_image_model": str_or_none(
            "openrouter_preferred_image_model"
        ),
        "openrouter_preferred_video_model": str_or_none(
            "openrouter_preferred_video_model"
        ),
    }
