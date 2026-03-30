from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str


class UploadResponse(BaseModel):
    success: bool
    filename: str
    content_type: str
    size: int
    data_url: str


class AccountUserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    points: int
    created_at: str


class AccountLedgerEntryResponse(BaseModel):
    id: str
    type: str
    amount: int
    balance_after: int
    description: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: AccountUserResponse
    ledger: list[AccountLedgerEntryResponse]
