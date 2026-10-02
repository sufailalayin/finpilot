import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.finance import AccountType, FinanceAccount, TransactionType
from app.models.user import User
from app.routers.finance import create_transfer
from app.schemas.finance import TransferCreate, TransferResponse


def _fake_account(user_id: uuid.UUID, name: str = "HDFC Bank") -> FinanceAccount:
    acc = FinanceAccount(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        account_type=AccountType.BANK,
        currency="INR",
        is_archived=False,
        opening_balance=Decimal("5000.00"),
    )
    return acc


def test_transfer_create_schema_accepts_outside_destination():
    acc_id = uuid.uuid4()
    payload = TransferCreate(
        from_account_id=acc_id,
        to_account_id=None,
        external_party="Vendor H",
        amount=Decimal("1250.75"),
        occurred_on=date(2026, 10, 2),
        note="Paid contractor",
    )
    assert payload.from_account_id == acc_id
    assert payload.to_account_id is None
    assert payload.external_party == "Vendor H"
    assert payload.amount == Decimal("1250.75")


def test_transfer_create_schema_accepts_outside_source():
    acc_id = uuid.uuid4()
    payload = TransferCreate(
        from_account_id=None,
        to_account_id=acc_id,
        external_party="Client Payment",
        amount=Decimal("50000.00"),
        occurred_on=date(2026, 10, 2),
    )
    assert payload.from_account_id is None
    assert payload.to_account_id == acc_id
    assert payload.external_party == "Client Payment"
    assert payload.amount == Decimal("50000.00")


def test_transfer_create_schema_rejects_zero_or_negative_amount():
    acc_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        TransferCreate(
            from_account_id=acc_id,
            to_account_id=None,
            amount=Decimal("0.00"),
            occurred_on=date(2026, 10, 2),
        )

    with pytest.raises(ValidationError):
        TransferCreate(
            from_account_id=acc_id,
            to_account_id=None,
            amount=Decimal("-100.00"),
            occurred_on=date(2026, 10, 2),
        )


@pytest.mark.asyncio
async def test_create_transfer_rejects_both_outside():
    user = User(id=uuid.uuid4(), email="tester@example.com")
    db = AsyncMock()
    payload = TransferCreate(
        from_account_id=None,
        to_account_id=None,
        amount=Decimal("100.00"),
        occurred_on=date(2026, 10, 2),
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_transfer(payload, user=user, db=db)

    assert exc_info.value.status_code == 400
    assert "At least one internal account" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_transfer_rejects_identical_accounts():
    user = User(id=uuid.uuid4(), email="tester@example.com")
    acc_id = uuid.uuid4()
    db = AsyncMock()
    payload = TransferCreate(
        from_account_id=acc_id,
        to_account_id=acc_id,
        amount=Decimal("100.00"),
        occurred_on=date(2026, 10, 2),
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_transfer(payload, user=user, db=db)

    assert exc_info.value.status_code == 400
    assert "different" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_transfer_internal_to_outside():
    user = User(id=uuid.uuid4(), email="tester@example.com")
    from_acc = _fake_account(user.id, "Main Bank")
    db = AsyncMock()
    db.add = MagicMock()
    db.scalar.return_value = from_acc

    payload = TransferCreate(
        from_account_id=from_acc.id,
        to_account_id=None,
        external_party="Amazon Seller",
        amount=Decimal("3450.50"),
        occurred_on=date(2026, 10, 2),
        note="Inventory order",
    )

    response = await create_transfer(payload, user=user, db=db)

    assert isinstance(response, TransferResponse)
    assert response.transfer_type == "outgoing_external"
    assert response.external_party == "Amazon Seller"
    assert response.incoming is None
    assert response.outgoing is not None
    assert response.outgoing.amount == Decimal("3450.50")
    assert response.outgoing.transaction_type == TransactionType.EXPENSE
    assert response.outgoing.is_internal_transfer is False
    assert "Amazon Seller" in (response.outgoing.merchant or "")


@pytest.mark.asyncio
async def test_create_transfer_outside_to_internal():
    user = User(id=uuid.uuid4(), email="tester@example.com")
    to_acc = _fake_account(user.id, "Cash Account")
    db = AsyncMock()
    db.add = MagicMock()
    db.scalar.return_value = to_acc

    payload = TransferCreate(
        from_account_id=None,
        to_account_id=to_acc.id,
        external_party="External ATM",
        amount=Decimal("2000.00"),
        occurred_on=date(2026, 10, 2),
        note="Withdrew physical cash",
    )

    response = await create_transfer(payload, user=user, db=db)

    assert isinstance(response, TransferResponse)
    assert response.transfer_type == "incoming_external"
    assert response.external_party == "External ATM"
    assert response.outgoing is None
    assert response.incoming is not None
    assert response.incoming.amount == Decimal("2000.00")
    assert response.incoming.transaction_type == TransactionType.INCOME
    assert response.incoming.is_internal_transfer is False
    assert "External ATM" in (response.incoming.merchant or "")


@pytest.mark.asyncio
async def test_create_transfer_internal_to_internal():
    user = User(id=uuid.uuid4(), email="tester@example.com")
    from_acc = _fake_account(user.id, "HDFC")
    to_acc = _fake_account(user.id, "SBI")
    to_acc.id = uuid.uuid4()

    db = AsyncMock()
    db.add_all = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [from_acc, to_acc]
    db.execute.return_value = mock_result

    payload = TransferCreate(
        from_account_id=from_acc.id,
        to_account_id=to_acc.id,
        amount=Decimal("1500.00"),
        occurred_on=date(2026, 10, 2),
        note="Self transfer",
    )

    response = await create_transfer(payload, user=user, db=db)

    assert isinstance(response, TransferResponse)
    assert response.transfer_type == "internal"
    assert response.outgoing is not None
    assert response.incoming is not None
    assert response.outgoing.amount == Decimal("1500.00")
    assert response.incoming.amount == Decimal("1500.00")
    assert response.outgoing.is_internal_transfer is True
    assert response.incoming.is_internal_transfer is True
