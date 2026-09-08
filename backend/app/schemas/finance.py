import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.finance import AccountType, TransactionType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    account_type: AccountType
    currency: str = Field(default="INR", min_length=3, max_length=3)
    opening_balance: Decimal = Decimal("0.00")


class AccountResponse(AccountCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    transaction_type: TransactionType


class CategoryResponse(CategoryCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    transaction_type: TransactionType
    amount: Decimal = Field(gt=0)
    occurred_on: date
    merchant: str | None = Field(default=None, max_length=120)
    note: str | None = None


class TransactionResponse(TransactionCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}
