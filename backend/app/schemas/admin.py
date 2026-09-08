from datetime import datetime
from pydantic import BaseModel


class AdminOverview(BaseModel):
    total_users: int
    active_trials: int
    paid_users: int
    expired_entitlements: int
    ai_requests: int


class AdminUserRow(BaseModel):
    id: str
    email: str
    full_name: str | None
    entitlement_status: str | None
    plan_code: str | None
    trial_ends_at: datetime | None
    paid_until: datetime | None
    created_at: datetime
