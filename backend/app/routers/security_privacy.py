from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.asset import Asset
from app.models.automation import BillReminder, RecurringRule
from app.models.finance import Category, FinanceAccount, Transaction
from app.models.liability import Liability, LiabilityPayment
from app.models.planning import Budget, SavingsGoal
from app.models.receivable import Receivable, ReceivableMovement, ReceivableRepayment
from app.models.user import SecurityAuditEvent, User
from app.schemas.security_privacy import (
    AccountDeleteRequest,
    DataExportResponse,
    RevokeSessionsResponse,
    SecurityEventResponse,
)

router = APIRouter(prefix="/security", tags=["security"])


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host[:64]
    return None


def _user_agent(request: Request) -> str | None:
    value = request.headers.get("user-agent")
    return value[:500] if value else None


def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return str(value)


def _model_row(instance) -> dict:
    return {
        column.name: _jsonable(getattr(instance, column.name))
        for column in instance.__table__.columns
    }


async def _rows(db: AsyncSession, model, user_id) -> list[dict]:
    result = await db.execute(select(model).where(model.user_id == user_id))
    return [_model_row(item) for item in result.scalars().all()]


@router.get("/events", response_model=list[SecurityEventResponse])
async def security_events(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SecurityEventResponse]:
    result = await db.execute(
        select(SecurityAuditEvent)
        .where(SecurityAuditEvent.user_id == user.id)
        .order_by(SecurityAuditEvent.created_at.desc())
        .limit(50)
    )
    return [
        SecurityEventResponse.model_validate(event)
        for event in result.scalars().all()
    ]


@router.post("/revoke-sessions", response_model=RevokeSessionsResponse)
async def revoke_sessions(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RevokeSessionsResponse:
    user.token_version += 1
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="sessions_revoked",
            description="All previous access tokens were revoked.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    return RevokeSessionsResponse(
        access_token=create_access_token(str(user.id), user.token_version)
    )


@router.get("/export", response_model=DataExportResponse)
async def export_account_data(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DataExportResponse:
    data = {
        "profile": _model_row(user),
        "accounts": await _rows(db, FinanceAccount, user.id),
        "categories": await _rows(db, Category, user.id),
        "transactions": await _rows(db, Transaction, user.id),
        "budgets": await _rows(db, Budget, user.id),
        "goals": await _rows(db, SavingsGoal, user.id),
        "recurring_rules": await _rows(db, RecurringRule, user.id),
        "bill_reminders": await _rows(db, BillReminder, user.id),
        "liabilities": await _rows(db, Liability, user.id),
        "liability_payments": await _rows(db, LiabilityPayment, user.id),
        "assets": await _rows(db, Asset, user.id),
        "receivables": await _rows(db, Receivable, user.id),
        "receivable_repayments": await _rows(db, ReceivableRepayment, user.id),
        "receivable_movements": await _rows(db, ReceivableMovement, user.id),
    }
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="data_exported",
            description="Account data export generated.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    return DataExportResponse(
        exported_at=datetime.now(timezone.utc),
        data=data,
    )


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    payload: AccountDeleteRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if payload.confirmation.strip().upper() != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Type "DELETE MY ACCOUNT" to confirm deletion',
        )
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect",
        )

    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="account_deleted",
            description="User requested permanent account deletion.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.flush()
    await db.delete(user)
    await db.commit()
