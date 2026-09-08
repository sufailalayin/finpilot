import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    period_start: date
    period_end: date
    category_id: uuid.UUID | None = None


class BudgetResponse(BudgetCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class SavingsGoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    target_date: date | None = None


class SavingsGoalResponse(SavingsGoalCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class GoalContribution(BaseModel):
    amount: Decimal = Field(gt=0)
