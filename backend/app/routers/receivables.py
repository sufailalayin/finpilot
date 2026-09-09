import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.entitlements import require_pro_user
from app.models.receivable import Receivable, ReceivableRepayment
from app.models.user import User
from app.schemas.receivable import (
    ReceivableCreate,
    ReceivableDetailResponse,
    ReceivableOverview,
    ReceivableRepaymentCreate,
    ReceivableRepaymentResponse,
    ReceivableResponse,
    ReceivableUpdate,
)

router = APIRouter(prefix="/receivables", tags=["receivables"])


def _serialize(item: Receivable) -> ReceivableResponse:
    remaining = max(
        Decimal("0.00"),
        item.original_amount - item.amount_received,
    )
    return ReceivableResponse(
        id=item.id,
        person_name=item.person_name,
        phone=item.phone,
        original_amount=item.original_amount,
        amount_received=item.amount_received,
        remaining_amount=remaining,
        status="cleared" if remaining <= 0 else "pending",
        given_on=item.given_on,
        due_on=item.due_on,
        note=item.note,
        created_at=item.created_at,
    )


@router.post("", response_model=ReceivableResponse, status_code=status.HTTP_201_CREATED)
async def create_receivable(
    payload: ReceivableCreate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> ReceivableResponse:
    if payload.due_on is not None and payload.due_on < payload.given_on:
        raise HTTPException(status_code=400, detail="Due date cannot be before given date")
    item = Receivable(
        user_id=user.id,
        person_name=payload.person_name.strip(),
        phone=payload.phone.strip() if payload.phone else None,
        original_amount=payload.original_amount,
        amount_received=Decimal("0.00"),
        given_on=payload.given_on,
        due_on=payload.due_on,
        note=payload.note.strip() if payload.note else None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _serialize(item)


@router.get("/overview", response_model=ReceivableOverview)
async def overview(
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> ReceivableOverview:
    rows = list(
        (
            await db.execute(
                select(Receivable)
                .where(Receivable.user_id == user.id)
                .order_by(Receivable.created_at.desc())
            )
        ).scalars().all()
    )
    pending = []
    cleared = []
    total_pending = Decimal("0.00")
    for row in rows:
        item = _serialize(row)
        if item.status == "cleared":
            cleared.append(item)
        else:
            pending.append(item)
            total_pending += item.remaining_amount
    return ReceivableOverview(
        total_pending=total_pending,
        pending_count=len(pending),
        cleared_count=len(cleared),
        pending=pending,
        cleared=cleared,
    )


@router.get("/{receivable_id}", response_model=ReceivableDetailResponse)
async def detail(
    receivable_id: uuid.UUID,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> ReceivableDetailResponse:
    item = await db.scalar(
        select(Receivable).where(
            Receivable.id == receivable_id,
            Receivable.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Receivable not found")
    payments = list(
        (
            await db.execute(
                select(ReceivableRepayment)
                .where(
                    ReceivableRepayment.receivable_id == item.id,
                    ReceivableRepayment.user_id == user.id,
                )
                .order_by(
                    ReceivableRepayment.received_on.desc(),
                    ReceivableRepayment.created_at.desc(),
                )
            )
        ).scalars().all()
    )
    base = _serialize(item)
    return ReceivableDetailResponse(
        **base.model_dump(),
        repayments=[
            ReceivableRepaymentResponse.model_validate(row)
            for row in payments
        ],
    )


@router.patch("/{receivable_id}", response_model=ReceivableResponse)
async def update_receivable(
    receivable_id: uuid.UUID,
    payload: ReceivableUpdate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> ReceivableResponse:
    item = await db.scalar(
        select(Receivable).where(
            Receivable.id == receivable_id,
            Receivable.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Receivable not found")
    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        if field in {"person_name", "phone", "note"} and isinstance(value, str):
            value = value.strip() or None
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return _serialize(item)


@router.post("/{receivable_id}/repayments", response_model=ReceivableRepaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_repayment(
    receivable_id: uuid.UUID,
    payload: ReceivableRepaymentCreate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> ReceivableRepaymentResponse:
    item = await db.scalar(
        select(Receivable).where(
            Receivable.id == receivable_id,
            Receivable.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Receivable not found")
    remaining = item.original_amount - item.amount_received
    if remaining <= 0:
        raise HTTPException(status_code=409, detail="This receivable is already cleared")
    if payload.amount > remaining:
        raise HTTPException(status_code=400, detail="Repayment exceeds pending amount")

    payment = ReceivableRepayment(
        receivable_id=item.id,
        user_id=user.id,
        amount=payload.amount,
        received_on=payload.received_on,
        note=payload.note.strip() if payload.note else None,
    )
    item.amount_received += payload.amount
    if item.amount_received >= item.original_amount:
        item.amount_received = item.original_amount

    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return ReceivableRepaymentResponse.model_validate(payment)


@router.delete("/{receivable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receivable(
    receivable_id: uuid.UUID,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    item = await db.scalar(
        select(Receivable).where(
            Receivable.id == receivable_id,
            Receivable.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Receivable not found")
    await db.delete(item)
    await db.commit()
