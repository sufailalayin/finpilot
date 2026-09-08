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


class RecurringRuleResponse(RecurringRuleCreate):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    due_on: date
    frequency: str = "once"


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
