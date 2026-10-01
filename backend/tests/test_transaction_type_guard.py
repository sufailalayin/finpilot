from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.finance import TransactionCreate, TransactionUpdate


def test_direct_transaction_schemas_accept_income_and_expense():
    common = {
        "account_id": uuid4(),
        "category_id": None,
        "amount": "10.00",
        "occurred_on": date.today(),
        "merchant": None,
        "note": None,
    }

    assert (
        TransactionCreate(transaction_type="income", **common).transaction_type.value
        == "income"
    )
    assert (
        TransactionCreate(transaction_type="expense", **common).transaction_type.value
        == "expense"
    )


def test_direct_transaction_schemas_reject_transfer():
    common = {
        "account_id": uuid4(),
        "category_id": None,
        "amount": "10.00",
        "occurred_on": date.today(),
        "merchant": None,
        "note": None,
    }

    with pytest.raises(ValidationError):
        TransactionCreate(transaction_type="transfer", **common)

    with pytest.raises(ValidationError):
        TransactionUpdate(transaction_type="transfer")
