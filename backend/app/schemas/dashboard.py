from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_balance: Decimal
    month_income: Decimal
    month_expense: Decimal
    month_net: Decimal
    transaction_count: int
    period_start: date
    period_end: date


class AccountBalance(BaseModel):
    account_id: str
    account_name: str
    currency: str
    balance: Decimal


class RecentTransaction(BaseModel):
    id: str
    account_name: str
    transaction_type: str
    amount: Decimal
    occurred_on: date
    merchant: str | None = None
    category_name: str | None = None


class DashboardInsight(BaseModel):
    title: str
    value: str
    subtitle: str | None = None
    severity: str = "info"


class DashboardAlert(BaseModel):
    title: str
    message: str
    severity: str
    due_on: date | None = None


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    accounts: list[AccountBalance]
    recent_transactions: list[RecentTransaction]
    net_worth: Decimal
    investment_assets: Decimal
    liabilities: Decimal
    savings_rate: float
    financial_health_score: int
    health_grade: str
    active_budget_count: int
    budget_warning_count: int
    upcoming_alert_count: int
    insights: list[DashboardInsight]
    alerts: list[DashboardAlert]
