from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.finance import AccountType, FinanceAccount
from app.schemas.finance import AccountCreate, AccountResponse
from app.services.finance_currency import (
    ensure_same_transfer_currency,
    ensure_supported_account_currency,
    ensure_supported_currencies,
)


def _account(currency: str, *, archived: bool = False) -> FinanceAccount:
    return FinanceAccount(
        user_id=uuid4(),
        name=f"{currency} account",
        account_type=AccountType.BANK,
        currency=currency,
        is_archived=archived,
        opening_balance=Decimal("0.00"),
    )


def test_account_create_normalizes_and_accepts_inr():
    payload = AccountCreate(
        name="Main Bank",
        account_type="bank",
        currency="inr",
    )

    assert payload.currency == "INR"


def test_account_create_rejects_unsupported_currency():
    with pytest.raises(ValidationError):
        AccountCreate(
            name="Dollar Bank",
            account_type="bank",
            currency="USD",
        )


def test_account_response_can_represent_legacy_currency():
    response = AccountResponse(
        id=uuid4(),
        name="Legacy Dollar Bank",
        account_type="bank",
        currency="USD",
        opening_balance=Decimal("100.00"),
        credit_limit=None,
        card_last4=None,
        statement_day=None,
        payment_due_day=None,
        created_at=datetime.now(timezone.utc),
    )

    assert response.currency == "USD"


def test_aggregate_currency_guard_accepts_inr_only():
    ensure_supported_currencies(["INR", "inr"])


def test_aggregate_currency_guard_rejects_legacy_non_inr():
    with pytest.raises(HTTPException) as exc_info:
        ensure_supported_currencies(["INR", "USD"])

    assert exc_info.value.status_code == 409
    assert "INR only" in str(exc_info.value.detail)


def test_supported_account_mutation_guard_rejects_legacy_non_inr():
    with pytest.raises(HTTPException) as exc_info:
        ensure_supported_account_currency(_account("USD"))

    assert exc_info.value.status_code == 409
    assert "New money movements" in str(exc_info.value.detail)


def test_supported_account_mutation_guard_accepts_inr():
    ensure_supported_account_currency(_account("inr"))


def test_transfer_currency_guard_rejects_cross_currency():
    with pytest.raises(HTTPException) as exc_info:
        ensure_same_transfer_currency(
            _account("INR"),
            _account("USD"),
        )

    assert exc_info.value.status_code == 409


def test_transfer_currency_guard_rejects_same_unsupported_currency():
    with pytest.raises(HTTPException) as exc_info:
        ensure_same_transfer_currency(
            _account("USD"),
            _account("USD"),
        )

    assert exc_info.value.status_code == 409
    assert "New money movements" in str(exc_info.value.detail)


def test_transfer_currency_guard_accepts_same_currency():
    ensure_same_transfer_currency(
        _account("INR"),
        _account("inr"),
    )



def test_supported_account_mutation_guard_rejects_archived_inr_account():
    with pytest.raises(HTTPException) as exc_info:
        ensure_supported_account_currency(_account("INR", archived=True))

    assert exc_info.value.status_code == 409
    assert "Archived legacy accounts" in str(exc_info.value.detail)
