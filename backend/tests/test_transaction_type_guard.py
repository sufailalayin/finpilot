import pytest
from fastapi import HTTPException

from app.models.finance import TransactionType
from app.routers.finance import _ensure_direct_transaction_type


def test_direct_transaction_type_guard_accepts_income_and_expense():
    _ensure_direct_transaction_type(TransactionType.INCOME)
    _ensure_direct_transaction_type(TransactionType.EXPENSE)
    _ensure_direct_transaction_type(None)


def test_direct_transaction_type_guard_rejects_transfer():
    with pytest.raises(HTTPException) as exc_info:
        _ensure_direct_transaction_type(TransactionType.TRANSFER)

    assert exc_info.value.status_code == 400
    assert "/finance/transfers" in str(exc_info.value.detail)
