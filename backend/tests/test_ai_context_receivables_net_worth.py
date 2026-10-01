import inspect
from decimal import Decimal

from app.services.ai_context import build_finance_context


def test_ai_wealth_summary_includes_outstanding_receivables():
    source = inspect.getsource(build_finance_context)

    assert "Receivable.original_amount - Receivable.amount_received" in source
    assert "Receivable.amount_received < Receivable.original_amount" in source
    assert '"receivables": str(receivables_total)' in source
    assert "account_total + asset_total + receivables_total - total_liabilities" in source


def test_ai_receivable_query_defaults_to_zero():
    source = inspect.getsource(build_finance_context)

    assert 'Decimal("0.00")' in source
    assert 'receivables_total = receivables_total or Decimal("0.00")' in source
