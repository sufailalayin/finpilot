from collections.abc import Iterable
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FinanceAccount

SUPPORTED_FINANCE_CURRENCY = "INR"


def normalize_currency(currency: str) -> str:
    return currency.strip().upper()


def ensure_supported_currencies(currencies: Iterable[str]) -> None:
    unsupported = sorted(
        {
            normalize_currency(currency)
            for currency in currencies
            if normalize_currency(currency) != SUPPORTED_FINANCE_CURRENCY
        }
    )
    if unsupported:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "FinPilot currently aggregates money in INR only. "
                "Unsupported account currency data must be converted before totals are calculated."
            ),
        )


def active_finance_account_ids(user_id: uuid.UUID):
    return select(FinanceAccount.id).where(
        FinanceAccount.user_id == user_id,
        FinanceAccount.is_archived.is_(False),
    )


def ensure_supported_account_currency(account: FinanceAccount) -> None:
    if account.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived legacy accounts cannot receive new money activity",
        )
    if normalize_currency(account.currency) != SUPPORTED_FINANCE_CURRENCY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "New money movements are only supported for INR accounts. "
                "Convert or remove the legacy account before recording new activity."
            ),
        )


async def ensure_user_finance_currency(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    rows = await db.scalars(
        select(FinanceAccount.currency).where(
            FinanceAccount.user_id == user_id,
            FinanceAccount.is_archived.is_(False),
        )
    )
    ensure_supported_currencies(rows.all())


def ensure_same_transfer_currency(
    from_account: FinanceAccount,
    to_account: FinanceAccount,
) -> None:
    ensure_supported_account_currency(from_account)
    ensure_supported_account_currency(to_account)
    if normalize_currency(from_account.currency) != normalize_currency(to_account.currency):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cross-currency transfers are not supported without FX conversion",
        )
