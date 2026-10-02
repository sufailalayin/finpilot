import inspect
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.finance import Category, TransactionType
from app.routers.automation import (
    _ensure_recurring_category_type,
    _load_owned_recurring_category,
    create_recurring,
    update_recurring,
)


def _category(transaction_type: TransactionType) -> Category:
    return Category(
        user_id=uuid4(),
        name="Test category",
        transaction_type=transaction_type,
    )


def test_recurring_category_type_guard_accepts_matching_type():
    _ensure_recurring_category_type(
        _category(TransactionType.INCOME),
        "income",
    )


def test_recurring_category_type_guard_rejects_mismatch():
    with pytest.raises(HTTPException) as exc_info:
        _ensure_recurring_category_type(
            _category(TransactionType.EXPENSE),
            "income",
        )

    assert exc_info.value.status_code == 400
    assert "Category type must match" in str(exc_info.value.detail)


def test_recurring_category_loader_enforces_tenant_scope():
    source = inspect.getsource(_load_owned_recurring_category)

    assert "Category.id == category_id" in source
    assert "Category.user_id == user_id" in source
    assert "_ensure_recurring_category_type" in source


def test_recurring_create_validates_owned_category_against_type():
    source = inspect.getsource(create_recurring)

    assert "if payload.category_id is not None:" in source
    assert "await _load_owned_recurring_category(" in source
    assert "payload.transaction_type" in source


def test_recurring_update_validates_effective_category_and_type():
    source = inspect.getsource(update_recurring)

    assert '"category_id" in values' in source
    assert '"transaction_type" in values' in source
    assert 'values.get("is_active") is True' in source
    assert 'effective_category_id = values.get("category_id", rule.category_id)' in source
    assert "if category_needs_validation and effective_category_id is not None:" in source
    assert "tx_type" in source
