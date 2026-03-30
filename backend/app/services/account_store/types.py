from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict


LedgerType = Literal["signup_bonus", "recharge", "generation", "refund"]
RechargeOrderStatus = Literal["pending", "paid", "failed", "expired"]


class LedgerEntry(TypedDict):
    id: str
    type: LedgerType
    amount: int
    balance_after: int
    description: str
    created_at: str


class UserRecord(TypedDict):
    id: str
    email: str
    display_name: str
    password_hash: str
    password_salt: str | None
    password_scheme: str
    points: int
    created_at: str
    openrouter_mode: str
    openrouter_api_key_encrypted: str | None
    openrouter_preferred_text_model: str | None
    openrouter_preferred_image_model: str | None
    openrouter_preferred_video_model: str | None


class OpenRouterSettingsRecord(TypedDict):
    mode: Literal["platform", "custom"]
    has_custom_key: bool
    key_mask: str | None
    preferred_models: dict[str, str | None]


OpenRouterPreferenceMap = dict[Literal["text", "image", "video"], str | None]


class PublicUserRecord(TypedDict):
    id: str
    email: str
    display_name: str
    points: int
    created_at: str
    openrouter: OpenRouterSettingsRecord


class SessionRecord(TypedDict):
    token: str
    token_hash: str
    user_id: str
    created_at: str
    expires_at: str


class RechargeRecord(TypedDict):
    payment_reference: str
    user_id: str
    package_id: str
    created_at: str


class RechargeOrderRecord(TypedDict):
    id: str
    user_id: str
    package_id: str
    provider: str
    out_trade_no: str
    status: RechargeOrderStatus
    amount_cny: int
    credits: int
    bonus_credits: int
    total_credits: int
    code_url: str | None
    payment_reference: str | None
    provider_payload: str | None
    created_at: str
    updated_at: str
    paid_at: str | None


class AccountStoreError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class RechargePackage:
    id: str
    label: str
    credits: int
    price_cny: int
    bonus_credits: int = 0

    @property
    def total_credits(self) -> int:
        return self.credits + self.bonus_credits


RECHARGE_PACKAGES: tuple[RechargePackage, ...] = (
    RechargePackage(
        id="starter", label="Starter", credits=200, price_cny=29, bonus_credits=20
    ),
    RechargePackage(
        id="creator", label="Creator", credits=500, price_cny=59, bonus_credits=80
    ),
    RechargePackage(
        id="studio", label="Studio", credits=1000, price_cny=109, bonus_credits=180
    ),
)


GENERATION_COSTS = {
    "image": 40,
    "text": 25,
    "video": 60,
}
