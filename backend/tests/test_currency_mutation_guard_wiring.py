import inspect

from app.routers.finance import create_transaction, update_transaction
from app.routers.liabilities import create_liability, record_payment, update_liability
from app.routers.receivables import create_movement, create_receivable, record_repayment


def _source(function) -> str:
    return inspect.getsource(function)


def test_transaction_mutations_apply_supported_account_currency_guard():
    assert "ensure_supported_account_currency" in _source(create_transaction)
    assert "ensure_supported_account_currency" in _source(update_transaction)


def test_receivable_mutations_apply_supported_account_currency_guard():
    assert "ensure_supported_account_currency" in _source(create_movement)
    assert "ensure_supported_account_currency" in _source(create_receivable)
    assert "ensure_supported_account_currency" in _source(record_repayment)


def test_liability_mutations_apply_supported_account_currency_guard():
    assert "ensure_supported_account_currency" in _source(create_liability)
    assert "ensure_supported_account_currency" in _source(update_liability)
    assert "ensure_supported_account_currency" in _source(record_payment)
