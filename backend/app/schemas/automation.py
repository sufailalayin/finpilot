import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RecurringRuleCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=120)
    transaction_type: str
    amount: Decimal = Field(gt=0)
    frequency: str = "monthly"
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    next_due_on: date


class RecurringRuleUpdate(BaseModel):
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    transaction_type: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    frequency: str | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    next_due_on: date | None = None
    is_active: bool | None = None


class RecurringRuleResponse(RecurringRuleCreate):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    bill_type: str = Field(default="bill", max_length=30)
    provider: str | None = Field(default=None, max_length=120)
    amount: Decimal = Field(gt=0)
    due_on: date
    bill_generated_on: date | None = None
    card_last4: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")
    frequency: str = "once"
    reminder_days_before: int = Field(default=3, ge=0, le=30)
    auto_renew: bool = False


class BillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    bill_type: str | None = Field(default=None, max_length=30)
    provider: str | None = Field(default=None, max_length=120)
    amount: Decimal | None = Field(default=None, gt=0)
    due_on: date | None = None
    bill_generated_on: date | None = None
    card_last4: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")
    frequency: str | None = None
    reminder_days_before: int | None = Field(default=None, ge=0, le=30)
    auto_renew: bool | None = None
    is_paid: bool | None = None


class BillResponse(BillCreate):
    id: uuid.UUID
    is_paid: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class AutomationOverview(BaseModel):
    recurring_income_30d: Decimal
    recurring_expense_30d: Decimal
    upcoming_bills_30d: Decimal
    projected_30d_net: Decimal
    recurring_rules: list[RecurringRuleResponse]
    bills: list[BillResponse]


class SmartAlert(BaseModel):
    alert_type: str
    severity: str
    title: str
    message: str
    due_on: date | None = None
    amount: Decimal | None = None
    source_id: uuid.UUID | None = None


class AlertOverview(BaseModel):
    critical_count: int
    warning_count: int
    info_count: int
    alerts: list[SmartAlert]
