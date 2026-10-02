import inspect

from app.services.ai_context import build_finance_context


def test_ai_cash_flow_context_excludes_internal_transfer_legs():
    source = inspect.getsource(build_finance_context)

    summary_section = source[source.index("summary_row ="):source.index("category_rows =")]
    category_section = source[source.index("category_rows ="):source.index("account_models =")]
    recent_section = source[source.index("recent_transactions ="):source.index("health =")]

    assert "Transaction.is_internal_transfer.is_(False)" in summary_section
    assert "Transaction.is_internal_transfer.is_(False)" in category_section
    assert "Transaction.is_internal_transfer.is_(False)" in recent_section


def test_ai_account_balance_movement_still_includes_internal_transfers():
    source = inspect.getsource(build_finance_context)
    account_section = source[source.index("for account in account_models:"):source.index("budgets =")]

    assert "Transaction.account_id == account.id" in account_section
    assert "Transaction.is_internal_transfer.is_(False)" not in account_section
