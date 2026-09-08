import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=140)
    asset_type: str = Field(min_length=1, max_length=40)
    institution: str | None = Field(default=None, max_length=140)
    quantity: Decimal = Field(default=Decimal("1.000000"), gt=0)
    cost_basis: Decimal = Field(default=Decimal("0.00"), ge=0)
    current_value: Decimal = Field(gt=0)
    maturity_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=140)
    asset_type: str | None = Field(default=None, min_length=1, max_length=40)
    institution: str | None = Field(default=None, max_length=140)
    quantity: Decimal | None = Field(default=None, gt=0)
    cost_basis: Decimal | None = Field(default=None, ge=0)
    current_value: Decimal | None = Field(default=None, gt=0)
    maturity_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)


class AssetResponse(BaseModel):
    id: uuid.UUID
    name: str
    asset_type: str
    institution: str | None
    quantity: Decimal
    cost_basis: Decimal
    current_value: Decimal
    maturity_date: date | None
    notes: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class AssetAllocation(BaseModel):
    asset_type: str
    value: Decimal
    percentage: float


class AssetOverview(BaseModel):
    total_assets: Decimal
    total_cost_basis: Decimal
    unrealized_gain: Decimal
    unrealized_gain_pct: float | None
    allocation: list[AssetAllocation]
    assets: list[AssetResponse]
