from datetime import datetime
from pydantic import BaseModel


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
