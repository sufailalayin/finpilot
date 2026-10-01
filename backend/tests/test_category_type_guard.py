from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.finance import Category, TransactionType
from app.routers.finance import _ensure_category_type


def _category(transaction_type: TransactionType) -> Category:
    return Category(
        user_id=uuid4(),
        name="Test category",
        transaction_type=transaction_type,
    )


def test_category_type_guard_accepts_matching_transaction_type():
    _ensure_category_type(
        _category(TransactionType.INCOME),
        TransactionType.INCOME,
    )
    _ensure_category_type(
        _category(TransactionType.EXPENSE),
        TransactionType.EXPENSE,
    )


@pytest.mark.parametrize(
    ("category_type", "transaction_type"),
    [
        (TransactionType.INCOME, TransactionType.EXPENSE),
        (TransactionType.EXPENSE, TransactionType.INCOME),
    ],
)
def test_category_type_guard_rejects_mismatch(category_type, transaction_type):
    with pytest.raises(HTTPException) as exc_info:
        _ensure_category_type(
            _category(category_type),
            transaction_type,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Category type must match transaction type"
