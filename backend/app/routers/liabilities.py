import uuid
from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.entitlements import require_pro_user
from app.models.finance import Transaction, TransactionType
from app.models.liability import Liability, LiabilityPayment
from app.models.user import User
from app.schemas.liability import (
    DebtOverview,
    LiabilityCreate,
    LiabilityPaymentCreate,
    LiabilityPaymentResponse,
    LiabilityResponse,
    LiabilityUpdate,
)

router = APIRouter(prefix="/liabilities", tags=["liabilities"])


@router.post("", response_model=LiabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_liability(
    payload: LiabilityCreate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> LiabilityResponse:
    if payload.outstanding_principal > payload.original_principal:
        raise HTTPException(status_code=400, detail="Outstanding principal cannot exceed original principal")
    item = Liability(user_id=user.id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return LiabilityResponse.model_validate(item)


@router.get("", response_model=list[LiabilityResponse])
async def list_liabilities(
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> list[LiabilityResponse]:
    result = await db.execute(
        select(Liability)
        .where(Liability.user_id == user.id)
        .order_by(Liability.outstanding_principal.desc(), Liability.created_at.asc())
    )
    return [LiabilityResponse.model_validate(row) for row in result.scalars().all()]


@router.patch("/{liability_id}", response_model=LiabilityResponse)
async def update_liability(
    liability_id: uuid.UUID,
    payload: LiabilityUpdate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> LiabilityResponse:
    item = await db.scalar(
        select(Liability).where(Liability.id == liability_id, Liability.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Liability not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "name" and value is not None:
            value = value.strip()
        setattr(item, field, value)
    if item.outstanding_principal > item.original_principal:
        raise HTTPException(status_code=400, detail="Outstanding principal cannot exceed original principal")
    await db.commit()
    await db.refresh(item)
    return LiabilityResponse.model_validate(item)


@router.delete("/{liability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_liability(
    liability_id: uuid.UUID,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    item = await db.scalar(
        select(Liability).where(Liability.id == liability_id, Liability.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Liability not found")
    await db.delete(item)
    await db.commit()


@router.post("/{liability_id}/payments", response_model=LiabilityPaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    liability_id: uuid.UUID,
    payload: LiabilityPaymentCreate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> LiabilityPaymentResponse:
    item = await db.scalar(
        select(Liability).where(Liability.id == liability_id, Liability.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Liability not found")
    if payload.principal_component > item.outstanding_principal:
        raise HTTPException(status_code=400, detail="Principal payment exceeds outstanding balance")
    if payload.principal_component + payload.interest_component > payload.amount:
        raise HTTPException(status_code=400, detail="Payment components exceed payment amount")

    payment = LiabilityPayment(
        liability_id=item.id,
        user_id=user.id,
        **payload.model_dump(),
    )
    item.outstanding_principal = max(
        Decimal("0.00"),
        item.outstanding_principal - payload.principal_component,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return LiabilityPaymentResponse.model_validate(payment)


@router.get("/overview/summary", response_model=DebtOverview)
async def debt_overview(
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> DebtOverview:
    liabilities = list(
        (
            await db.execute(
                select(Liability)
                .where(Liability.user_id == user.id)
                .order_by(Liability.outstanding_principal.desc())
            )
        ).scalars().all()
    )

    total_outstanding = sum((x.outstanding_principal for x in liabilities), Decimal("0.00"))
    total_original = sum((x.original_principal for x in liabilities), Decimal("0.00"))
    monthly_emi = sum((x.emi_amount for x in liabilities), Decimal("0.00"))

    today = date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])
    monthly_income = await db.scalar(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            )
        ).where(
            Transaction.user_id == user.id,
            Transaction.occurred_on >= start,
            Transaction.occurred_on <= end,
        )
    )
    monthly_income = monthly_income or Decimal("0.00")

    dti = round(float(monthly_emi / monthly_income * 100), 1) if monthly_income > 0 else None
    payoff = (
        round(float((total_original - total_outstanding) / total_original * 100), 1)
        if total_original > 0
        else 0.0
    )

    return DebtOverview(
        total_outstanding=total_outstanding,
        total_original_principal=total_original,
        monthly_emi_commitment=monthly_emi,
        monthly_income=monthly_income,
        debt_to_income_pct=dti,
        payoff_progress_pct=payoff,
        liabilities=[LiabilityResponse.model_validate(x) for x in liabilities],
    )
