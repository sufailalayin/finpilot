from datetime import datetime
from decimal import Decimal
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
    unverified_users: int


class AdminUserRow(BaseModel):
    id: str
    email: str
    full_name: str | None
    user_status: str
    is_admin: bool
    email_verified: bool
    entitlement_status: str | None
    plan_code: str | None
    billing_plan_id: str | None = None
    billing_plan_name: str | None = None
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
    billing_plan_id: str | None = None
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


class AdminBillingPlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    access_level: str = Field(default="pro", pattern=r"^(free|pro)$")
    billing_period: str = Field(default="monthly", pattern=r"^(monthly|quarterly|yearly|lifetime|custom)$")
    price: Decimal = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=1000)
    features: dict | None = None
    is_active: bool = True


class AdminBillingPlanRow(AdminBillingPlanCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class AdminPaymentCreate(BaseModel):
    user_id: str
    billing_plan_id: str | None = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_method: str = Field(min_length=2, max_length=40)
    provider: str | None = Field(default=None, max_length=40)
    reference: str | None = Field(default=None, max_length=160)
    status: str = Field(default="received", pattern=r"^(received|pending|refunded|failed)$")
    notes: str | None = Field(default=None, max_length=1000)
    received_at: datetime
    reason: str = Field(min_length=3, max_length=300)


class AdminPaymentRow(BaseModel):
    id: str
    user_id: str
    user_email: str
    billing_plan_id: str | None
    billing_plan_name: str | None
    amount: Decimal
    currency: str
    payment_method: str
    provider: str | None
    reference: str | None
    status: str
    notes: str | None
    received_at: datetime
    recorded_by_admin_email: str | None
    created_at: datetime


class AdminUserLocationUpdate(BaseModel):
    country: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    reason: str = Field(min_length=3, max_length=300)


class AdminUserDetail(BaseModel):
    user: AdminUserRow
    country: str | None
    state: str | None
    city: str | None
    postal_code: str | None
    last_ip_address: str | None
    last_user_agent: str | None
    location_updated_at: datetime | None
    payments: list[AdminPaymentRow]


class AdminDeleteUserRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=300)
    confirmation: str = Field(pattern=r"^DELETE$")



class AppReleaseUpdate(BaseModel):
    latest_version: str = Field(min_length=1, max_length=40)
    latest_build_number: int = Field(ge=1)
    minimum_version: str = Field(min_length=1, max_length=40)
    minimum_build_number: int = Field(ge=1)
    update_url: str | None = Field(default=None, max_length=1000)
    release_notes: str | None = Field(default=None, max_length=5000)
    distribution: str = Field(default="apk", pattern=r"^(apk|play_store)$")
    is_update_enabled: bool = True


class AppReleaseResponse(AppReleaseUpdate):
    updated_at: datetime
