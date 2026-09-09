from datetime import datetime
from pydantic import BaseModel, Field


class AdminOverview(BaseModel):
    total_users: int
    active_trials: int
    paid_users: int
    expired_entitlements: int
    ai_requests: int
    registrations_7d: int
    finance_accounts: int
    transactions: int
    assets: int
    liabilities: int
    security_events_24h: int


class AdminUserRow(BaseModel):
    id: str
    email: str
    full_name: str | None
    user_status: str
    is_admin: bool
    entitlement_status: str | None
    plan_code: str | None
    trial_ends_at: datetime | None
    paid_until: datetime | None
    created_at: datetime


class AdminSubscriptionSummary(BaseModel):
    free_users: int
    trial_users: int
    active_paid_users: int
    cancelled_users: int
    expired_users: int


class AdminAIUsageSummary(BaseModel):
    total_requests: int
    requests_24h: int
    requests_7d: int
    unique_users_7d: int
    prompt_chars_7d: int
    response_chars_7d: int


class AdminSecurityEventRow(BaseModel):
    id: str
    user_id: str | None
    user_email: str | None
    event_type: str
    description: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AdminUserUpdate(BaseModel):
    user_status: str | None = None
    plan_code: str | None = None
    entitlement_status: str | None = None
    trial_ends_at: datetime | None = None
    paid_until: datetime | None = None
    reason: str = Field(min_length=3, max_length=300)


class AdminActionLogRow(BaseModel):
    id: str
    actor_admin_id: str | None
    actor_admin_email: str | None
    target_user_id: str | None
    target_user_email: str | None
    action: str
    reason: str
    before_state: dict | None
    after_state: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
