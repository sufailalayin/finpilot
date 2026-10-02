import inspect

from app.services.ai_context import build_finance_context


def test_ai_display_lists_can_remain_limited():
    source = inspect.getsource(build_finance_context)

    assert ".limit(20)" in source
    assert ".limit(30)" in source


def test_ai_wealth_totals_use_uncapped_database_aggregates():
    source = inspect.getsource(build_finance_context)

    assert "func.sum(Asset.current_value)" in source
    assert "func.sum(Liability.outstanding_principal)" in source
    assert "sum((row.current_value for row in assets)" not in source
    assert "sum(\n        (row.outstanding_principal for row in liabilities)" not in source
