"""Backward-compatible account_store package.

Every symbol that was previously importable from
``app.services.account_store`` is re-exported here so that existing
callers continue to work without changes.
"""

from app.services.account_store.store import AccountStore
from app.services.account_store.types import (
    GENERATION_COSTS,
    RECHARGE_PACKAGES,
    AccountStoreError,
    LedgerEntry,
    LedgerType,
    OpenRouterPreferenceMap,
    OpenRouterSettingsRecord,
    PublicUserRecord,
    RechargeOrderRecord,
    RechargeOrderStatus,
    RechargePackage,
    RechargeRecord,
    SessionRecord,
    UserRecord,
)

# Module-level singleton – matches the old ``account_store = AccountStore()``
# at the bottom of the original monolithic module.
account_store = AccountStore()

__all__ = [
    "GENERATION_COSTS",
    "RECHARGE_PACKAGES",
    "AccountStore",
    "AccountStoreError",
    "LedgerEntry",
    "LedgerType",
    "OpenRouterPreferenceMap",
    "OpenRouterSettingsRecord",
    "PublicUserRecord",
    "RechargeOrderRecord",
    "RechargeOrderStatus",
    "RechargePackage",
    "RechargeRecord",
    "SessionRecord",
    "UserRecord",
    "account_store",
]
