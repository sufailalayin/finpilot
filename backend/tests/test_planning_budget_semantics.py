import inspect
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.finance import Category, TransactionType
from app.routers.planning import (
    _ensure_budget_category_type,
    _load_owned_expense_category,
    budget_dashboard,
    create_budget,
    update_budget,
)


def _category(transaction_type: TransactionType) -> Category:
    return Category(
        user_id=uuid4(),
        name="Test category",
        transaction_type=transaction_type,
    )


def test_budget_category_type_guard_accepts_expense():
    _ensure_budget_category_type(_category(TransactionType.EXPENSE))


def test_budget_category_type_guard_rejects_income():
    with pytest.raises(HTTPException) as exc_info:
        _ensure_budget_category_type(_category(TransactionType.INCOME))

    assert exc_info.value.status_code == 400
    assert "expense category" in str(exc_info.value.detail)


def test_budget_category_loader_enforces_tenant_scope():
    source = inspect.getsource(_load_owned_expense_category)

    assert "Category.id == category_id" in source
    assert "Category.user_id == user_id" in source
    assert "_ensure_budget_category_type(category)" in source


def test_budget_create_and_update_use_expense_category_loader():
    assert "await _load_owned_expense_category(" in inspect.getsource(create_budget)
    assert "await _load_owned_expense_category(" in inspect.getsource(update_budget)


def test_budget_dashboard_excludes_internal_transfers():
    source = inspect.getsource(budget_dashboard)

    assert "Transaction.is_internal_transfer.is_(False)" in source
    assert "Transaction.account_id.in_(active_finance_account_ids(user.id))" in source
