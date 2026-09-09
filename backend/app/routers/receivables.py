import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.entitlements import require_pro_user
from app.models.finance import FinanceAccount, Transaction, TransactionType
from app.models.receivable import Receivable, ReceivableMovement, ReceivableRepayment
from app.models.liability import Liability, LiabilityPayment
from app.models.user import User
from app.schemas.receivable import (
    ReceivableCreate,
    ReceivableDetailResponse,
    ReceivableOverview,
    ReceivableRepaymentCreate,
    ReceivableMovementCreate,
    ReceivableMovementResponse,
    ReceivableRepaymentResponse,
    ReceivableResponse,
    ReceivableUpdate,
)

router = APIRouter(prefix="/receivables", tags=["receivables"])


async def _available_account_balance(
    db: AsyncSession,
    user_id,
    account: FinanceAccount,
) -> Decimal:
    tx_movement = await db.scalar(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                        (Transaction.transaction_type == TransactionType.EXPENSE, -Transaction.amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            )
        ).where(
            Transaction.user_id == user_id,
            Transaction.account_id == account.id,
        )
    )
    receivable_movement = await db.scalar(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (ReceivableMovement.destination_account_id == account.id, ReceivableMovement.amount),
                        (ReceivableMovement.source_account_id == account.id, -ReceivableMovement.amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            )
        ).where(ReceivableMovement.user_id == user_id)
    )
    liability_inflow = await db.scalar(
        select(
            func.coalesce(func.sum(Liability.original_principal), Decimal("0.00"))
        ).where(
            Liability.user_id == user_id,
            Liability.funding_account_id == account.id,
        )
    )
    liability_outflow = await db.scalar(
        select(
            func.coalesce(func.sum(LiabilityPayment.amount), Decimal("0.00"))
        ).where(
            LiabilityPayment.user_id == user_id,
            LiabilityPayment.payment_account_id == account.id,
        )
    )
    return (
        account.opening_balance
        + (tx_movement or Decimal("0.00"))
        + (receivable_movement or Decimal("0.00"))
        + (liability_inflow or Decimal("0.00"))
        - (liability_outflow or Decimal("0.00"))
    )


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


@router.post("/movements", response_model=ReceivableMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_movement(
    payload: ReceivableMovementCreate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> ReceivableMovementResponse:
    if payload.source_type == payload.destination_type == "outside":
        raise HTTPException(status_code=400, detail="Outside to outside movement is not tracked")
    if payload.source_type != "person" and payload.destination_type != "person":
        raise HTTPException(status_code=400, detail="At least one side must be a person")
    if (
        payload.source_type == "person"
        and payload.destination_type == "person"
        and payload.source_receivable_id == payload.destination_receivable_id
    ):
        raise HTTPException(status_code=400, detail="Source and destination person must be different")
    if payload.source_type == "account" and payload.source_account_id is None:
        raise HTTPException(status_code=400, detail="Source account is required")
    if payload.destination_type == "account" and payload.destination_account_id is None:
        raise HTTPException(status_code=400, detail="Destination account is required")
    if payload.source_type == "person" and payload.source_receivable_id is None:
        raise HTTPException(status_code=400, detail="Source person is required")
    if payload.destination_type == "person" and payload.destination_receivable_id is None:
        raise HTTPException(status_code=400, detail="Destination person is required")

    source_account = None
    destination_account = None
    source_person = None
    destination_person = None

    if payload.source_account_id is not None:
        source_account = await db.scalar(
            select(FinanceAccount).where(
                FinanceAccount.id == payload.source_account_id,
                FinanceAccount.user_id == user.id,
            )
        )
        if source_account is None:
            raise HTTPException(status_code=404, detail="Source account not found")
        if source_account.account_type.value not in {"cash", "bank"}:
            raise HTTPException(status_code=400, detail="Source must be Cash or Bank")
        available = await _available_account_balance(db, user.id, source_account)
        if payload.amount > available:
            raise HTTPException(
                status_code=400,
                detail="Selected account does not have enough balance",
            )

    if payload.destination_account_id is not None:
        destination_account = await db.scalar(
            select(FinanceAccount).where(
                FinanceAccount.id == payload.destination_account_id,
                FinanceAccount.user_id == user.id,
            )
        )
        if destination_account is None:
            raise HTTPException(status_code=404, detail="Destination account not found")
        if destination_account.account_type.value not in {"cash", "bank"}:
            raise HTTPException(status_code=400, detail="Destination must be Cash or Bank")

    if payload.source_receivable_id is not None:
        source_person = await db.scalar(
            select(Receivable).where(
                Receivable.id == payload.source_receivable_id,
                Receivable.user_id == user.id,
            )
        )
        if source_person is None:
            raise HTTPException(status_code=404, detail="Source person not found")

    if payload.destination_receivable_id is not None:
        destination_person = await db.scalar(
            select(Receivable).where(
                Receivable.id == payload.destination_receivable_id,
                Receivable.user_id == user.id,
            )
        )
        if destination_person is None:
            raise HTTPException(status_code=404, detail="Destination person not found")

    if source_person is not None:
        remaining = source_person.original_amount - source_person.amount_received
        if payload.amount > remaining:
            raise HTTPException(status_code=400, detail="Amount exceeds source person's pending balance")
        source_person.amount_received += payload.amount

    if destination_person is not None:
        destination_person.original_amount += payload.amount

    movement = ReceivableMovement(
        user_id=user.id,
        **payload.model_dump(),
    )
    db.add(movement)
    await db.commit()
    await db.refresh(movement)
    return ReceivableMovementResponse.model_validate(movement, from_attributes=True)


@router.get("/movements", response_model=list[ReceivableMovementResponse])
async def list_movements(
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReceivableMovementResponse]:
    rows = list(
        (
            await db.execute(
                select(ReceivableMovement)
                .where(ReceivableMovement.user_id == user.id)
                .order_by(
                    ReceivableMovement.occurred_on.desc(),
                    ReceivableMovement.created_at.desc(),
                )
            )
        ).scalars().all()
    )
    return [
        ReceivableMovementResponse.model_validate(row, from_attributes=True)
        for row in rows
    ]


@router.post("", response_model=ReceivableResponse, status_code=status.HTTP_201_CREATED)
async def create_receivable(
    payload: ReceivableCreate,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> ReceivableResponse:
    if payload.due_on is not None and payload.due_on < payload.given_on:
        raise HTTPException(status_code=400, detail="Due date cannot be before given date")
    if payload.source_type == "account" and payload.source_account_id is None:
        raise HTTPException(status_code=400, detail="Source account is required")

    source_account = None
    if payload.source_account_id is not None:
        source_account = await db.scalar(
            select(FinanceAccount).where(
                FinanceAccount.id == payload.source_account_id,
                FinanceAccount.user_id == user.id,
            )
        )
        if source_account is None:
            raise HTTPException(status_code=404, detail="Source account not found")
        if source_account.account_type.value not in {"cash", "bank"}:
            raise HTTPException(status_code=400, detail="Money can only be given from Cash or Bank")
        available = await _available_account_balance(db, user.id, source_account)
        if payload.original_amount > available:
            raise HTTPException(
                status_code=400,
                detail="Selected account does not have enough balance",
            )

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
    await db.flush()

    db.add(
        ReceivableMovement(
            user_id=user.id,
            source_type=payload.source_type,
            destination_type="person",
            source_account_id=payload.source_account_id,
            destination_account_id=None,
            source_receivable_id=None,
            destination_receivable_id=item.id,
            amount=payload.original_amount,
            occurred_on=payload.given_on,
            note=payload.note.strip() if payload.note else None,
        )
    )

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

    if payload.destination_type == "account" and payload.destination_account_id is None:
        raise HTTPException(status_code=400, detail="Destination account is required")

    if payload.destination_account_id is not None:
        destination_account = await db.scalar(
            select(FinanceAccount).where(
                FinanceAccount.id == payload.destination_account_id,
                FinanceAccount.user_id == user.id,
            )
        )
        if destination_account is None:
            raise HTTPException(status_code=404, detail="Destination account not found")

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
    db.add(
        ReceivableMovement(
            user_id=user.id,
            source_type="person",
            destination_type=payload.destination_type,
            source_account_id=None,
            destination_account_id=payload.destination_account_id,
            source_receivable_id=item.id,
            destination_receivable_id=None,
            amount=payload.amount,
            occurred_on=payload.received_on,
            note=payload.note.strip() if payload.note else None,
        )
    )
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
