import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import (
    AssetAllocation,
    AssetCreate,
    AssetOverview,
    AssetResponse,
    AssetUpdate,
)

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    item = Asset(user_id=user.id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return AssetResponse.model_validate(item)


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AssetResponse]:
    result = await db.execute(
        select(Asset)
        .where(Asset.user_id == user.id)
        .order_by(Asset.current_value.desc(), Asset.created_at.asc())
    )
    return [AssetResponse.model_validate(row) for row in result.scalars().all()]


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    item = await db.scalar(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "name" and value is not None:
            value = value.strip()
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return AssetResponse.model_validate(item)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    item = await db.scalar(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(item)
    await db.commit()


@router.get("/overview/summary", response_model=AssetOverview)
async def asset_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetOverview:
    assets = list(
        (
            await db.execute(
                select(Asset)
                .where(Asset.user_id == user.id)
                .order_by(Asset.current_value.desc())
            )
        ).scalars().all()
    )

    total_assets = sum((x.current_value for x in assets), Decimal("0.00"))
    total_cost = sum((x.cost_basis for x in assets), Decimal("0.00"))
    gain = total_assets - total_cost
    gain_pct = round(float(gain / total_cost * 100), 1) if total_cost > 0 else None

    grouped: dict[str, Decimal] = {}
    for item in assets:
        grouped[item.asset_type] = grouped.get(item.asset_type, Decimal("0.00")) + item.current_value

    allocation = [
        AssetAllocation(
            asset_type=asset_type,
            value=value,
            percentage=round(float(value / total_assets * 100), 1) if total_assets > 0 else 0.0,
        )
        for asset_type, value in sorted(grouped.items(), key=lambda row: row[1], reverse=True)
    ]

    return AssetOverview(
        total_assets=total_assets,
        total_cost_basis=total_cost,
        unrealized_gain=gain,
        unrealized_gain_pct=gain_pct,
        allocation=allocation,
        assets=[AssetResponse.model_validate(x) for x in assets],
    )
