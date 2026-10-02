from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class AdminPaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


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


class AdminPaginatedUsers(BaseModel):
    items: list[AdminUserRow]
    meta: AdminPaginationMeta


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


class AdminPaginatedSecurityEvents(BaseModel):
    items: list[AdminSecurityEventRow]
    meta: AdminPaginationMeta


class AdminUserUpdate(BaseModel):
    full_name: str | None = None
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


class AdminPaginatedActionLogs(BaseModel):
    items: list[AdminActionLogRow]
    meta: AdminPaginationMeta


class AdminBillingPlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    access_level: str = Field(default="pro", pattern=r"^(free|pro)$")
    billing_period: str = Field(default="monthly", pattern=r"^(monthly|quarterly|yearly|lifetime|custom)$")
    google_play_product_id: str | None = Field(default=None, max_length=160)
    price: Decimal = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=1000)
    features: dict | None = None
    is_active: bool = True


class AdminBillingPlanRow(AdminBillingPlanCreate):
    id: str
    active_subscribers_count: int = 0
    created_at: datetime
    updated_at: datetime


class AdminBillingPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    access_level: str | None = Field(default=None, pattern=r"^(free|pro)$")
    billing_period: str | None = Field(default=None, pattern=r"^(monthly|quarterly|yearly|lifetime|custom)$")
    google_play_product_id: str | None = Field(default=None, max_length=160)
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=1000)
    features: dict | None = None
    is_active: bool | None = None
    reason: str = Field(min_length=3, max_length=300)


class AdminPaymentCreate(BaseModel):
    user_id: str
    billing_plan_id: str | None = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_method: str = Field(min_length=2, max_length=40)
    provider: str | None = Field(default=None, max_length=40)
    reference: str | None = Field(default=None, max_length=160)
    status: str = Field(default="received", pattern=r"^(received|pending|refunded|voided|failed)$")
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


class AdminPaginatedPayments(BaseModel):
    items: list[AdminPaymentRow]
    meta: AdminPaginationMeta


class AdminPaymentUpdate(BaseModel):
    payment_method: str | None = Field(default=None, min_length=2, max_length=40)
    provider: str | None = Field(default=None, max_length=40)
    reference: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)
    reason: str = Field(min_length=3, max_length=300)


class AdminPaymentVoidRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


class AdminUserLocationUpdate(BaseModel):
    country: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    reason: str = Field(min_length=3, max_length=300)


class AdminUserFinancialSummary(BaseModel):
    accounts_count: int
    transactions_count: int
    assets_count: int
    liabilities_count: int
    last_activity_date: datetime | None = None


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
    financial_summary: AdminUserFinancialSummary
    recent_security_events: list[AdminSecurityEventRow]
    recent_admin_actions: list[AdminActionLogRow]
    active_sessions_count: int


class AdminDeleteUserRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=300)
    confirmation: str = Field(pattern=r"^DELETE(\s+[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})?$")


class AppReleaseUpdate(BaseModel):
    latest_version: str = Field(min_length=1, max_length=40)
    latest_build_number: int = Field(ge=1)
    minimum_version: str = Field(min_length=1, max_length=40)
    minimum_build_number: int = Field(ge=1)
    update_url: str | None = Field(default=None, max_length=1000)
    release_notes: str | None = Field(default=None, max_length=5000)
    distribution: str = Field(default="apk", pattern=r"^(apk|play_store)$")
    is_update_enabled: bool = True

    @field_validator("update_url")
    @classmethod
    def validate_update_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        candidate = value.strip()
        if not candidate:
            return None
        if not candidate.startswith("https://"):
            raise ValueError("Update URL must use HTTPS")
        return candidate


class AppReleaseResponse(AppReleaseUpdate):
    updated_at: datetime


# --- Admin V2 Analytics Schemas ---

class AdminAnalyticsOverview(BaseModel):
    total_users: int
    active_users: int
    new_users_today: int
    new_users_7d: int
    new_users_30d: int
    active_trials: int
    paid_users: int
    free_users: int
    expired_users: int
    suspended_users: int
    revenue_today: Decimal
    revenue_this_month: Decimal
    revenue_this_year: Decimal
    total_recorded_revenue: Decimal
    ai_requests_today: int
    ai_requests_7d: int
    security_events_24h: int
    failed_login_attempts: int
    unverified_emails: int
    finance_accounts: int
    transactions: int


class UserGrowthPoint(BaseModel):
    date: str
    registrations: int
    cumulative: int


class AdminAnalyticsUsers(BaseModel):
    period: str
    points: list[UserGrowthPoint]
    total_registrations: int


class RevenuePoint(BaseModel):
    date: str
    revenue: Decimal
    count: int
    voided_amount: Decimal


class AdminAnalyticsRevenue(BaseModel):
    period: str
    points: list[RevenuePoint]
    total_revenue: Decimal
    total_transactions: int
    voided_revenue: Decimal


class PlanDistributionItem(BaseModel):
    plan_id: str | None = None
    plan_code: str
    plan_name: str
    count: int
    percentage: float


class PaymentMethodDistributionItem(BaseModel):
    method: str
    count: int
    amount: Decimal
    percentage: float


class TrialConversionMetrics(BaseModel):
    trials_started: int
    trials_active: int
    trials_converted: int
    trials_expired: int
    conversion_rate_pct: float


class AdminAnalyticsSubscriptions(BaseModel):
    distribution: dict[str, int]
    by_plan: list[PlanDistributionItem]
    trial_conversion: TrialConversionMetrics
    payment_methods: list[PaymentMethodDistributionItem]


class AIUsagePoint(BaseModel):
    date: str
    requests: int
    prompt_chars: int
    response_chars: int


class AITopUser(BaseModel):
    user_id: str
    user_email: str
    requests: int


class AdminAnalyticsAI(BaseModel):
    total_requests: int
    requests_24h: int
    requests_7d: int
    requests_30d: int
    unique_users_7d: int
    points: list[AIUsagePoint]
    top_users: list[AITopUser]


class SecurityBreakdownItem(BaseModel):
    event_type: str
    count: int


class SecurityTrendPoint(BaseModel):
    date: str
    total: int
    logins: int
    failures: int


class AdminAnalyticsSecurity(BaseModel):
    period: str
    total_events: int
    failed_logins: int
    breakdown: list[SecurityBreakdownItem]
    points: list[SecurityTrendPoint]
