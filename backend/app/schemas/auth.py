import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import EntitlementStatus, PlanCode


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EntitlementResponse(BaseModel):
    plan_code: PlanCode
    status: EntitlementStatus
    trial_ends_at: datetime | None
    paid_until: datetime | None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_admin: bool
    created_at: datetime
    entitlement: EntitlementResponse | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
