import inspect

from app.routers.automation import (
    _load_owned_supported_account,
    create_bill,
    create_credit_card_statement,
    update_bill,
)


def _source(function) -> str:
    return inspect.getsource(function)


def test_owned_account_loader_enforces_tenant_and_currency_boundary():
    source = _source(_load_owned_supported_account)

    assert "FinanceAccount.id == account_id" in source
    assert "FinanceAccount.user_id == user_id" in source
    assert "ensure_supported_account_currency(account)" in source


def test_bill_create_validates_linked_account_but_allows_unlinked_bill():
    source = _source(create_bill)

    assert "if payload.account_id is not None:" in source
    assert "await _load_owned_supported_account(" in source


def test_bill_update_validates_account_reassignment_and_allows_unlink():
    source = _source(update_bill)

    assert '"account_id" in values and values["account_id"] is not None' in source
    assert "await _load_owned_supported_account(" in source


def test_credit_card_statement_creation_uses_owned_supported_account():
    source = _source(create_credit_card_statement)

    assert "await _load_owned_supported_account(" in source
    assert 'account.account_type.value != "card"' in source
