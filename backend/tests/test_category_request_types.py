from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.finance import CategoryCreate, CategoryResponse


def test_category_create_accepts_income_and_expense():
    assert CategoryCreate(
        name="Salary",
        transaction_type="income",
    ).transaction_type.value == "income"
    assert CategoryCreate(
        name="Food",
        transaction_type="expense",
    ).transaction_type.value == "expense"


def test_category_create_rejects_transfer():
    with pytest.raises(ValidationError):
        CategoryCreate(
            name="Internal transfer",
            transaction_type="transfer",
        )


def test_category_response_can_represent_legacy_transfer_value():
    response = CategoryResponse(
        id=uuid4(),
        name="Legacy transfer",
        transaction_type="transfer",
        created_at=datetime.now(timezone.utc),
    )

    assert response.transaction_type.value == "transfer"
