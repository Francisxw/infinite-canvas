from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock

from cryptography.fernet import Fernet, InvalidToken
from passlib.hash import pbkdf2_sha256
from passlib.exc import UnknownHashError

from app.config import derive_account_secret_key, get_settings
from app.services.account_store.transform import (
    _row_to_openrouter_settings,
    hash_legacy_password,
    hash_session_token,
    now_iso,
    package_payload,
    row_to_public_user,
    row_to_recharge_order,
    row_to_user_record,
)
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
    UserRecord,
)


class AccountStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._file_path = Path(settings.account_data_file)
        self._signup_bonus_points = settings.signup_bonus_points
        self._session_ttl_hours = settings.account_session_ttl_hours
        self._cipher = Fernet(derive_account_secret_key(settings.account_secret))
        self._lock = Lock()

    def _ensure_parent(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        self._ensure_parent()
        connection = sqlite3.connect(
            self._file_path,
            timeout=10.0,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        self._ensure_schema(connection)
        self._migrate_legacy_json_if_needed(connection)
        return connection

    def _begin_immediate(self, connection: sqlite3.Connection) -> None:
        connection.execute("BEGIN IMMEDIATE")

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT,
                password_scheme TEXT NOT NULL DEFAULT 'pbkdf2_sha256',
                points INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                openrouter_mode TEXT NOT NULL DEFAULT 'platform',
                openrouter_api_key_encrypted TEXT,
                openrouter_preferred_text_model TEXT,
                openrouter_preferred_image_model TEXT,
                openrouter_preferred_video_model TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                token_hash TEXT,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ledger_entries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recharge_records (
                payment_reference TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                package_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recharge_orders (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                package_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                out_trade_no TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                amount_cny INTEGER NOT NULL,
                credits INTEGER NOT NULL,
                bonus_credits INTEGER NOT NULL,
                total_credits INTEGER NOT NULL,
                code_url TEXT,
                payment_reference TEXT,
                provider_payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                paid_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
            CREATE INDEX IF NOT EXISTS idx_ledger_user_id_created_at ON ledger_entries(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_recharge_orders_user_id_created_at ON recharge_orders(user_id, created_at DESC);
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "password_salt" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN password_salt TEXT")
        if "password_scheme" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN password_scheme TEXT NOT NULL DEFAULT 'pbkdf2_sha256'"
            )
        if "openrouter_mode" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN openrouter_mode TEXT NOT NULL DEFAULT 'platform'"
            )
        if "openrouter_api_key_encrypted" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN openrouter_api_key_encrypted TEXT"
            )
        if "openrouter_preferred_text_model" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN openrouter_preferred_text_model TEXT"
            )
        if "openrouter_preferred_image_model" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN openrouter_preferred_image_model TEXT"
            )
        if "openrouter_preferred_video_model" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN openrouter_preferred_video_model TEXT"
            )
        if (
            "openrouter_preferred_model" in columns
            and "openrouter_preferred_image_model" in columns
        ):
            connection.execute(
                "UPDATE users SET openrouter_preferred_image_model = openrouter_preferred_model WHERE openrouter_preferred_image_model IS NULL AND openrouter_preferred_model IS NOT NULL"
            )
        session_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
        }
        if "expires_at" not in session_columns:
            connection.execute("ALTER TABLE sessions ADD COLUMN expires_at TEXT")
            connection.execute(
                "UPDATE sessions SET expires_at = ? WHERE expires_at IS NULL",
                (self._session_expires_at(),),
            )
        if "token_hash" not in session_columns:
            connection.execute("ALTER TABLE sessions ADD COLUMN token_hash TEXT")
        stale_session_tokens = connection.execute(
            "SELECT token FROM sessions WHERE token_hash IS NULL"
        ).fetchall()
        for row in stale_session_tokens:
            token_value = row["token"]
            if token_value is None:
                continue
            connection.execute(
                "UPDATE sessions SET token_hash = ? WHERE token = ?",
                (hash_session_token(str(token_value)), str(token_value)),
            )
        connection.commit()

    def _parse_timestamp(self, value: str | None) -> datetime:
        if not value:
            return datetime.now(UTC)

        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.now(UTC)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _session_expires_at(self, created_at: str | None = None) -> str:
        base = self._parse_timestamp(created_at) if created_at else datetime.now(UTC)
        return (base + timedelta(hours=self._session_ttl_hours)).isoformat()

    def _prune_expired_sessions(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            "DELETE FROM sessions WHERE expires_at <= ?",
            (now_iso(),),
        )

    def _create_session(self, connection: sqlite3.Connection, user_id: str) -> str:
        token = f"session_{secrets.token_hex(16)}"
        token_hash = hash_session_token(token)
        connection.execute(
            "INSERT INTO sessions (token, token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (token, token_hash, user_id, now_iso(), self._session_expires_at()),
        )
        return token

    def _migrate_legacy_json_if_needed(self, connection: sqlite3.Connection) -> None:
        legacy_json_path = self._file_path.with_suffix(".json")

        if not legacy_json_path.exists() or legacy_json_path == self._file_path:
            return

        try:
            legacy_payload = json.loads(legacy_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AccountStoreError(
                "account_store_corrupt", "Legacy account storage is invalid.", 500
            ) from exc

        users = legacy_payload.get("users", [])
        sessions = legacy_payload.get("sessions", [])
        recharges = legacy_payload.get("recharges", [])

        with connection:
            self._begin_immediate(connection)
            for user in users:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO users (id, email, display_name, password_hash, password_salt, password_scheme, points, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user.get("id"),
                        user.get("email"),
                        user.get("display_name"),
                        user.get("password_hash"),
                        user.get("password_salt"),
                        "legacy_sha256"
                        if user.get("password_salt")
                        else "pbkdf2_sha256",
                        int(user.get("points", 0)),
                        user.get("created_at"),
                    ),
                )

                for entry in user.get("ledger", []):
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO ledger_entries (id, user_id, type, amount, balance_after, description, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            entry.get("id"),
                            user.get("id"),
                            entry.get("type"),
                            int(entry.get("amount", 0)),
                            int(entry.get("balance_after", 0)),
                            entry.get("description"),
                            entry.get("created_at"),
                        ),
                    )

            for session in sessions:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO sessions (token, token_hash, user_id, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        session.get("token"),
                        hash_session_token(str(session.get("token")))
                        if session.get("token")
                        else None,
                        session.get("user_id"),
                        session.get("created_at"),
                        session.get("expires_at")
                        or self._session_expires_at(session.get("created_at")),
                    ),
                )

            for recharge in recharges:
                payment_reference = recharge.get("payment_reference")
                if not payment_reference:
                    continue
                connection.execute(
                    """
                    INSERT OR IGNORE INTO recharge_records (payment_reference, user_id, package_id, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        payment_reference,
                        recharge.get("user_id"),
                        recharge.get("package_id"),
                        recharge.get("created_at"),
                    ),
                )

    def _get_user_by_email(
        self, connection: sqlite3.Connection, email: str
    ) -> sqlite3.Row | None:
        self._prune_expired_sessions(connection)
        return connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

    def _get_user_by_id(
        self, connection: sqlite3.Connection, user_id: str
    ) -> sqlite3.Row | None:
        self._prune_expired_sessions(connection)
        return connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    def _get_user_by_token(
        self, connection: sqlite3.Connection, token: str
    ) -> sqlite3.Row | None:
        self._prune_expired_sessions(connection)
        token_hash = hash_session_token(token)
        row = connection.execute(
            """
            SELECT users.*
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
            """,
            (token_hash, now_iso()),
        ).fetchone()
        if row:
            return row

        return connection.execute(
            """
            SELECT users.*
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ? AND sessions.expires_at > ?
            """,
            (token, now_iso()),
        ).fetchone()

    def _list_ledger(
        self, connection: sqlite3.Connection, user_id: str
    ) -> list[LedgerEntry]:
        rows = connection.execute(
            """
            SELECT id, type, amount, balance_after, description, created_at
            FROM ledger_entries
            WHERE user_id = ?
            ORDER BY created_at DESC, rowid DESC
            LIMIT 80
            """,
            (user_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "type": row["type"],
                "amount": row["amount"],
                "balance_after": row["balance_after"],
                "description": row["description"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def _get_recharge_order_by_id(
        self, connection: sqlite3.Connection, order_id: str
    ) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM recharge_orders WHERE id = ?",
            (order_id,),
        ).fetchone()

    def _get_recharge_order_by_trade_no(
        self, connection: sqlite3.Connection, out_trade_no: str
    ) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM recharge_orders WHERE out_trade_no = ?",
            (out_trade_no,),
        ).fetchone()

    def _record_ledger(
        self,
        connection: sqlite3.Connection,
        *,
        user_id: str,
        amount: int,
        entry_type: LedgerType,
        description: str,
    ) -> PublicUserRecord:
        row = self._get_user_by_id(connection, user_id)
        if not row:
            raise AccountStoreError("user_not_found", "Account not found.", 404)

        next_balance = int(row["points"]) + amount
        connection.execute(
            "UPDATE users SET points = ? WHERE id = ?",
            (next_balance, user_id),
        )
        connection.execute(
            """
            INSERT INTO ledger_entries (id, user_id, type, amount, balance_after, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"ledger_{secrets.token_hex(6)}",
                user_id,
                entry_type,
                amount,
                next_balance,
                description,
                now_iso(),
            ),
        )
        updated = self._get_user_by_id(connection, user_id)
        if not updated:
            raise AccountStoreError("user_not_found", "Account not found.", 404)
        return row_to_public_user(updated)

    def register(
        self, *, email: str, password: str, display_name: str
    ) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                normalized_email = email.strip().lower()
                if self._get_user_by_email(connection, normalized_email):
                    raise AccountStoreError(
                        "email_exists", "This email is already registered.", 409
                    )

                user_id = f"user_{secrets.token_hex(6)}"
                created_at = now_iso()
                password_hash = pbkdf2_sha256.hash(password)

                with connection:
                    self._begin_immediate(connection)
                    connection.execute(
                        """
                        INSERT INTO users (id, email, display_name, password_hash, password_salt, password_scheme, points, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            normalized_email,
                            display_name.strip(),
                            password_hash,
                            None,
                            "pbkdf2_sha256",
                            0,
                            created_at,
                        ),
                    )
                    public_user = self._record_ledger(
                        connection,
                        user_id=user_id,
                        amount=self._signup_bonus_points,
                        entry_type="signup_bonus",
                        description="Registration bonus credited.",
                    )
                    token = self._create_session(connection, user_id)

                return {
                    "token": token,
                    "user": public_user,
                    "ledger": self._list_ledger(connection, user_id),
                }
            finally:
                connection.close()

    def login(self, *, email: str, password: str) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                user = self._get_user_by_email(connection, email)
                if not user:
                    raise AccountStoreError(
                        "invalid_credentials", "Invalid email or password.", 401
                    )

                password_scheme = user["password_scheme"] or "pbkdf2_sha256"
                if password_scheme == "legacy_sha256":
                    password_salt = user["password_salt"] or ""
                    verified = (
                        hash_legacy_password(password, password_salt)
                        == user["password_hash"]
                    )
                else:
                    try:
                        verified = pbkdf2_sha256.verify(password, user["password_hash"])
                    except (ValueError, TypeError, UnknownHashError):
                        verified = False

                if not verified:
                    raise AccountStoreError(
                        "invalid_credentials", "Invalid email or password.", 401
                    )

                with connection:
                    self._begin_immediate(connection)
                    if password_scheme == "legacy_sha256":
                        connection.execute(
                            "UPDATE users SET password_hash = ?, password_salt = NULL, password_scheme = 'pbkdf2_sha256' WHERE id = ?",
                            (pbkdf2_sha256.hash(password), user["id"]),
                        )
                    connection.execute(
                        "DELETE FROM sessions WHERE user_id = ?", (user["id"],)
                    )
                    token = self._create_session(connection, str(user["id"]))

                user = self._get_user_by_id(connection, user["id"])
                if not user:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)

                return {
                    "token": token,
                    "user": row_to_public_user(user),
                    "ledger": self._list_ledger(connection, user["id"]),
                }
            finally:
                connection.close()

    def resolve_token(self, token: str) -> PublicUserRecord:
        with self._lock:
            connection = self._connect()
            try:
                user = self._get_user_by_token(connection, token)
                if not user:
                    raise AccountStoreError(
                        "auth_required", "Please sign in to continue.", 401
                    )
                return row_to_public_user(user)
            finally:
                connection.close()

    def get_full_user(self, user_id: str) -> UserRecord:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_user_by_id(connection, user_id)
                if not row:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)
                return row_to_user_record(row)
            finally:
                connection.close()

    def get_user_by_token(self, token: str) -> UserRecord:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_user_by_token(connection, token)
                if not row:
                    raise AccountStoreError(
                        "auth_required", "Please sign in to continue.", 401
                    )
                return row_to_user_record(row)
            finally:
                connection.close()

    def logout(self, token: str) -> None:
        with self._lock:
            connection = self._connect()
            try:
                with connection:
                    self._begin_immediate(connection)
                    connection.execute(
                        "DELETE FROM sessions WHERE token_hash = ? OR token = ?",
                        (hash_session_token(token), token),
                    )
            finally:
                connection.close()

    def get_profile(self, user_id: str) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_user_by_id(connection, user_id)
                if not row:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)
                return {
                    "user": row_to_public_user(row),
                    "ledger": self._list_ledger(connection, user_id),
                }
            finally:
                connection.close()

    def get_account_settings(self, user_id: str) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_user_by_id(connection, user_id)
                if not row:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)
                return {
                    "user": row_to_public_user(row),
                    "settings": _row_to_openrouter_settings(row),
                }
            finally:
                connection.close()

    def update_account_settings(
        self,
        *,
        user_id: str,
        openrouter_mode: str,
        openrouter_api_key: str | None,
        preferred_models: OpenRouterPreferenceMap | None,
    ) -> dict[str, object]:
        normalized_mode = "custom" if openrouter_mode == "custom" else "platform"
        normalized_key = openrouter_api_key.strip() if openrouter_api_key else None
        text_model = preferred_models.get("text") if preferred_models else None
        image_model = preferred_models.get("image") if preferred_models else None
        video_model = preferred_models.get("video") if preferred_models else None
        normalized_models = {
            "text": text_model.strip()
            if isinstance(text_model, str) and text_model
            else None,
            "image": image_model.strip()
            if isinstance(image_model, str) and image_model
            else None,
            "video": video_model.strip()
            if isinstance(video_model, str) and video_model
            else None,
        }

        if (
            normalized_mode == "custom"
            and normalized_key is not None
            and not normalized_key.startswith("sk-or-v1-")
        ):
            raise AccountStoreError(
                "invalid_openrouter_key",
                "OpenRouter 密钥格式不正确，应以 sk-or-v1- 开头。",
                400,
            )

        with self._lock:
            connection = self._connect()
            try:
                row = self._get_user_by_id(connection, user_id)
                if not row:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)

                next_encrypted_key = row["openrouter_api_key_encrypted"]
                if normalized_key:
                    next_encrypted_key = self._cipher.encrypt(
                        normalized_key.encode("utf-8")
                    ).decode("utf-8")

                if normalized_mode == "custom" and not next_encrypted_key:
                    raise AccountStoreError(
                        "openrouter_key_required",
                        "切换到自定义 OpenRouter 前，请先保存一个有效密钥。",
                        400,
                    )

                with connection:
                    self._begin_immediate(connection)
                    connection.execute(
                        "UPDATE users SET openrouter_mode = ?, openrouter_api_key_encrypted = ?, openrouter_preferred_text_model = ?, openrouter_preferred_image_model = ?, openrouter_preferred_video_model = ? WHERE id = ?",
                        (
                            normalized_mode,
                            next_encrypted_key,
                            normalized_models["text"],
                            normalized_models["image"],
                            normalized_models["video"],
                            user_id,
                        ),
                    )

                updated = self._get_user_by_id(connection, user_id)
                if not updated:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)

                return {
                    "user": row_to_public_user(updated),
                    "settings": _row_to_openrouter_settings(updated),
                }
            finally:
                connection.close()

    def get_openrouter_credentials(
        self, user_id: str
    ) -> tuple[str | None, dict[str, str | None]]:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_user_by_id(connection, user_id)
                if not row:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)

                encrypted_key = row["openrouter_api_key_encrypted"]
                decrypted_key = None
                if encrypted_key:
                    try:
                        decrypted_key = self._cipher.decrypt(
                            str(encrypted_key).encode("utf-8")
                        ).decode("utf-8")
                    except (InvalidToken, ValueError, TypeError) as exc:
                        raise AccountStoreError(
                            "openrouter_key_unreadable",
                            "保存的 OpenRouter 密钥无法解密，请重新配置。",
                            500,
                        ) from exc

                return decrypted_key, {
                    "text": None
                    if row["openrouter_preferred_text_model"] is None
                    else str(row["openrouter_preferred_text_model"]),
                    "image": None
                    if row["openrouter_preferred_image_model"] is None
                    else str(row["openrouter_preferred_image_model"]),
                    "video": None
                    if row["openrouter_preferred_video_model"] is None
                    else str(row["openrouter_preferred_video_model"]),
                }
            finally:
                connection.close()

    def list_packages(self) -> list[dict[str, object]]:
        return [package_payload(item) for item in RECHARGE_PACKAGES]

    def create_recharge_order(
        self, *, user_id: str, package_id: str, provider: str
    ) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                user = self._get_user_by_id(connection, user_id)
                if not user:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)

                selected = next(
                    (item for item in RECHARGE_PACKAGES if item.id == package_id), None
                )
                if not selected:
                    raise AccountStoreError(
                        "package_not_found", "Recharge package not found.", 404
                    )

                created_at = now_iso()
                order_id = f"order_{secrets.token_hex(6)}"
                out_trade_no = f"IC{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4)}"

                with connection:
                    self._begin_immediate(connection)
                    connection.execute(
                        """
                        INSERT INTO recharge_orders (
                            id, user_id, package_id, provider, out_trade_no, status,
                            amount_cny, credits, bonus_credits, total_credits,
                            code_url, payment_reference, provider_payload,
                            created_at, updated_at, paid_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            order_id,
                            user_id,
                            selected.id,
                            provider,
                            out_trade_no,
                            "pending",
                            selected.price_cny,
                            selected.credits,
                            selected.bonus_credits,
                            selected.total_credits,
                            None,
                            None,
                            None,
                            created_at,
                            created_at,
                            None,
                        ),
                    )

                row = self._get_recharge_order_by_id(connection, order_id)
                if not row:
                    raise AccountStoreError(
                        "order_not_found", "Recharge order not found.", 404
                    )
                return {
                    "order": row_to_recharge_order(row),
                    "package": package_payload(selected),
                    "user": row_to_public_user(user),
                }
            finally:
                connection.close()

    def set_recharge_order_code_url(
        self,
        *,
        order_id: str,
        code_url: str,
        provider_payload: dict[str, object] | None = None,
    ) -> RechargeOrderRecord:
        with self._lock:
            connection = self._connect()
            try:
                with connection:
                    self._begin_immediate(connection)
                    connection.execute(
                        "UPDATE recharge_orders SET code_url = ?, provider_payload = ?, updated_at = ? WHERE id = ?",
                        (
                            code_url,
                            json.dumps(provider_payload, ensure_ascii=True)
                            if provider_payload
                            else None,
                            now_iso(),
                            order_id,
                        ),
                    )

                row = self._get_recharge_order_by_id(connection, order_id)
                if not row:
                    raise AccountStoreError(
                        "order_not_found", "Recharge order not found.", 404
                    )
                return row_to_recharge_order(row)
            finally:
                connection.close()

    def update_recharge_order_status(
        self,
        *,
        order_id: str,
        status: RechargeOrderStatus,
        provider_payload: dict[str, object] | None = None,
    ) -> RechargeOrderRecord:
        with self._lock:
            connection = self._connect()
            try:
                with connection:
                    self._begin_immediate(connection)
                    connection.execute(
                        "UPDATE recharge_orders SET status = ?, provider_payload = ?, updated_at = ? WHERE id = ?",
                        (
                            status,
                            json.dumps(provider_payload, ensure_ascii=True)
                            if provider_payload
                            else None,
                            now_iso(),
                            order_id,
                        ),
                    )

                row = self._get_recharge_order_by_id(connection, order_id)
                if not row:
                    raise AccountStoreError(
                        "order_not_found", "Recharge order not found.", 404
                    )
                return row_to_recharge_order(row)
            finally:
                connection.close()

    def get_recharge_order(self, *, user_id: str, order_id: str) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_recharge_order_by_id(connection, order_id)
                if not row or row["user_id"] != user_id:
                    raise AccountStoreError(
                        "order_not_found", "Recharge order not found.", 404
                    )
                user = self._get_user_by_id(connection, user_id)
                if not user:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)
                return {
                    "order": row_to_recharge_order(row),
                    "user": row_to_public_user(user),
                    "ledger": self._list_ledger(connection, user_id),
                }
            finally:
                connection.close()

    def get_recharge_order_by_trade_no(
        self, out_trade_no: str
    ) -> RechargeOrderRecord | None:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_recharge_order_by_trade_no(connection, out_trade_no)
                return row_to_recharge_order(row) if row else None
            finally:
                connection.close()

    def mark_recharge_order_paid(
        self,
        *,
        out_trade_no: str,
        payment_reference: str,
        provider_payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                row = self._get_recharge_order_by_trade_no(connection, out_trade_no)
                if not row:
                    raise AccountStoreError(
                        "order_not_found", "Recharge order not found.", 404
                    )

                if row["status"] == "paid":
                    user = self._get_user_by_id(connection, row["user_id"])
                    if not user:
                        raise AccountStoreError(
                            "user_not_found", "Account not found.", 404
                        )
                    return {
                        "order": row_to_recharge_order(row),
                        "user": row_to_public_user(user),
                        "ledger": self._list_ledger(connection, row["user_id"]),
                    }

                if row["status"] in {"failed", "expired"}:
                    raise AccountStoreError(
                        "order_state_invalid",
                        "Recharge order is not payable.",
                        409,
                    )

                with connection:
                    self._begin_immediate(connection)
                    try:
                        connection.execute(
                            "INSERT INTO recharge_records (payment_reference, user_id, package_id, created_at) VALUES (?, ?, ?, ?)",
                            (
                                payment_reference,
                                row["user_id"],
                                row["package_id"],
                                now_iso(),
                            ),
                        )
                    except sqlite3.IntegrityError as exc:
                        raise AccountStoreError(
                            "duplicate_payment_reference",
                            "This payment reference has already been processed.",
                            409,
                        ) from exc

                    selected = next(
                        (
                            item
                            for item in RECHARGE_PACKAGES
                            if item.id == row["package_id"]
                        ),
                        None,
                    )
                    public_user = self._record_ledger(
                        connection,
                        user_id=row["user_id"],
                        amount=int(row["total_credits"]),
                        entry_type="recharge",
                        description=f"Recharge package {(selected.label if selected else row['package_id'])} credited.",
                    )
                    paid_at = now_iso()
                    connection.execute(
                        "UPDATE recharge_orders SET status = 'paid', payment_reference = ?, provider_payload = ?, updated_at = ?, paid_at = ? WHERE id = ?",
                        (
                            payment_reference,
                            json.dumps(provider_payload, ensure_ascii=True)
                            if provider_payload
                            else None,
                            paid_at,
                            paid_at,
                            row["id"],
                        ),
                    )

                updated = self._get_recharge_order_by_id(connection, row["id"])
                if not updated:
                    raise AccountStoreError(
                        "order_not_found", "Recharge order not found.", 404
                    )
                return {
                    "order": row_to_recharge_order(updated),
                    "user": public_user,
                    "ledger": self._list_ledger(connection, row["user_id"]),
                }
            finally:
                connection.close()

    def recharge(
        self, *, user_id: str, package_id: str, payment_reference: str
    ) -> dict[str, object]:
        with self._lock:
            connection = self._connect()
            try:
                selected = next(
                    (item for item in RECHARGE_PACKAGES if item.id == package_id), None
                )
                if not selected:
                    raise AccountStoreError(
                        "package_not_found", "Recharge package not found.", 404
                    )

                user = self._get_user_by_id(connection, user_id)
                if not user:
                    raise AccountStoreError("user_not_found", "Account not found.", 404)

                existing = connection.execute(
                    "SELECT payment_reference FROM recharge_records WHERE payment_reference = ?",
                    (payment_reference,),
                ).fetchone()
                if existing:
                    raise AccountStoreError(
                        "duplicate_payment_reference",
                        "This payment reference has already been processed.",
                        409,
                    )

                with connection:
                    self._begin_immediate(connection)
                    try:
                        connection.execute(
                            """
                            INSERT INTO recharge_records (payment_reference, user_id, package_id, created_at)
                            VALUES (?, ?, ?, ?)
                            """,
                            (payment_reference, user_id, selected.id, now_iso()),
                        )
                    except sqlite3.IntegrityError as exc:
                        raise AccountStoreError(
                            "duplicate_payment_reference",
                            "This payment reference has already been processed.",
                            409,
                        ) from exc

                    public_user = self._record_ledger(
                        connection,
                        user_id=user_id,
                        amount=selected.total_credits,
                        entry_type="recharge",
                        description=f"Recharge package {selected.label} credited.",
                    )

                return {
                    "user": public_user,
                    "ledger": self._list_ledger(connection, user_id),
                    "package": package_payload(selected),
                }
            finally:
                connection.close()

    def consume_points(
        self, *, user_id: str, amount: int, description: str
    ) -> PublicUserRecord:
        with self._lock:
            connection = self._connect()
            try:
                with connection:
                    self._begin_immediate(connection)

                    row = self._get_user_by_id(connection, user_id)
                    if not row:
                        raise AccountStoreError(
                            "user_not_found", "Account not found.", 404
                        )
                    if int(row["points"]) < amount:
                        raise AccountStoreError(
                            "insufficient_points",
                            "Insufficient points, please recharge first.",
                            402,
                        )

                    return self._record_ledger(
                        connection,
                        user_id=user_id,
                        amount=-amount,
                        entry_type="generation",
                        description=description,
                    )
            finally:
                connection.close()

    def refund_points(
        self, *, user_id: str, amount: int, description: str
    ) -> PublicUserRecord:
        with self._lock:
            connection = self._connect()
            try:
                if not self._get_user_by_id(connection, user_id):
                    raise AccountStoreError("user_not_found", "Account not found.", 404)

                with connection:
                    self._begin_immediate(connection)
                    return self._record_ledger(
                        connection,
                        user_id=user_id,
                        amount=amount,
                        entry_type="refund",
                        description=description,
                    )
            finally:
                connection.close()
