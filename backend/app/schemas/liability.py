import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class LiabilityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=140)
    liability_type: str = Field(min_length=1, max_length=40)
    lender: str | None = Field(default=None, max_length=140)
    original_principal: Decimal = Field(gt=0)
    outstanding_principal: Decimal = Field(gt=0)
    interest_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    emi_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    next_due_on: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    funding_account_id: uuid.UUID | None = None
    funding_account_id: uuid.UUID | None = None


class LiabilityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=140)
    liability_type: str | None = Field(default=None, min_length=1, max_length=40)
    lender: str | None = Field(default=None, max_length=140)
    outstanding_principal: Decimal | None = Field(default=None, ge=0)
    interest_rate: Decimal | None = Field(default=None, ge=0)
    emi_amount: Decimal | None = Field(default=None, ge=0)
    next_due_on: date | None = None
    end_date: date | None = None


class LiabilityResponse(BaseModel):
    id: uuid.UUID
    name: str
    liability_type: str
    lender: str | None
    original_principal: Decimal
    outstanding_principal: Decimal
    interest_rate: Decimal
    emi_amount: Decimal
    next_due_on: date | None
    start_date: date | None
    end_date: date | None
    funding_account_id: uuid.UUID | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class LiabilityPaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    principal_component: Decimal = Field(gt=0)
    interest_component: Decimal = Field(default=Decimal("0.00"), ge=0)
    paid_on: date
    note: str | None = Field(default=None, max_length=300)
    payment_account_id: uuid.UUID | None = None


class LiabilityPaymentResponse(LiabilityPaymentCreate):
    id: uuid.UUID
    liability_id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class DebtOverview(BaseModel):
    total_outstanding: Decimal
    total_original_principal: Decimal
    monthly_emi_commitment: Decimal
    monthly_income: Decimal
    debt_to_income_pct: float | None
    payoff_progress_pct: float
    liabilities: list[LiabilityResponse]
