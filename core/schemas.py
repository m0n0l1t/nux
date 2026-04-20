from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ---- Auth Schemas ----
class UserRegisterRequest(BaseModel):
    invite_code: str = Field(..., min_length=1, description="Invite code")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=6, description="Password")


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TelegramRegisterRequest(BaseModel):
    invite_code: str = Field(..., min_length=1, description="Invite code для регистрации через Telegram")


class LinkCredentialsRequest(BaseModel):
    invite_code: str = Field(..., min_length=1, description="Invite code (тот же, что использовался в боте)")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=6, description="Password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    message: str
    user_id: int


# ---- Proxy Schemas ----
class ProxyServiceResponse(BaseModel):
    id: int
    name: str
    expiration_date: datetime
    proxy_link: Optional[str]
    days_left: int



# ---- WireGuard Schemas ----
class WireGuardCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Service name")


class WireGuardResponse(BaseModel):
    id: int
    name: str
    expiration_date: datetime
    days_left: int
    address: str
    public_key: str


class WireGuardListResponse(BaseModel):
    id: int
    name: str
    expiration_date: datetime
    days_left: int
    address: Optional[str]
    public_key: Optional[str]


# ---- Invite Schemas ----
class InviteCreateRequest(BaseModel):
    expires_at: Optional[datetime] = None


class InviteResponse(BaseModel):
    id: int
    code: str
    creator_user_id: int
    used_by_user_id: Optional[int]
    created_at: datetime
    used_at: Optional[datetime]
    expires_at: Optional[datetime]


# ---- Admin Schemas ----
class AdminInviteCreateRequest(BaseModel):
    expires_at: Optional[datetime] = None
    x_admin_uuid: str = Field(..., description="Admin UUID for authorization")


class AdminTopUpRequest(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    amount_stars: float = Field(..., gt=0, description="Amount to add in Telegram Stars")


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


# ---- Billing Schemas ----
class BalanceResponse(BaseModel):
    balance_stars: float
    username: str


class PaymentRecord(BaseModel):
    id: int
    user_id: int
    telegram_payment_id: Optional[str]
    amount_stars: float
    status: str
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentHistoryResponse(BaseModel):
    payments: list[PaymentRecord]


class TopUpRequest(BaseModel):
    amount_stars: int = Field(..., ge=1, description="Amount in Telegram Stars")
