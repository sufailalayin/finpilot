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


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    account_type: AccountType | None = None
    opening_balance: Decimal | None = None


class AccountBalanceResponse(BaseModel):
    id: uuid.UUID
    name: str
    account_type: AccountType
    currency: str
    opening_balance: Decimal
    current_balance: Decimal
    created_at: datetime


class AccountResponse(AccountCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    transaction_type: TransactionType


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)


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


class TransactionUpdate(BaseModel):
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    transaction_type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    occurred_on: date | None = None
    merchant: str | None = Field(default=None, max_length=120)
    note: str | None = None


class TransferCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    occurred_on: date
    note: str | None = None


class TransferResponse(BaseModel):
    outgoing: TransactionResponse
    incoming: TransactionResponse


class NetWorthResponse(BaseModel):
    account_assets: Decimal
    investment_assets: Decimal
    total_assets: Decimal
    liabilities: Decimal
    net_worth: Decimal
