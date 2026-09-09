import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReceivableCreate(BaseModel):
    person_name: str = Field(min_length=1, max_length=140)
    phone: str | None = Field(default=None, max_length=30)
    original_amount: Decimal = Field(gt=0)
    given_on: date
    due_on: date | None = None
    note: str | None = Field(default=None, max_length=500)


class ReceivableUpdate(BaseModel):
    person_name: str | None = Field(default=None, min_length=1, max_length=140)
    phone: str | None = Field(default=None, max_length=30)
    due_on: date | None = None
    note: str | None = Field(default=None, max_length=500)


class ReceivableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_name: str
    phone: str | None
    original_amount: Decimal
    amount_received: Decimal
    remaining_amount: Decimal
    status: str
    given_on: date
    due_on: date | None
    note: str | None
    created_at: datetime


class ReceivableRepaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    received_on: date
    note: str | None = Field(default=None, max_length=300)


class ReceivableRepaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    receivable_id: uuid.UUID
    amount: Decimal
    received_on: date
    note: str | None
    created_at: datetime


class ReceivableDetailResponse(ReceivableResponse):
    repayments: list[ReceivableRepaymentResponse]


class ReceivableOverview(BaseModel):
    total_pending: Decimal
    pending_count: int
    cleared_count: int
    pending: list[ReceivableResponse]
    cleared: list[ReceivableResponse]
