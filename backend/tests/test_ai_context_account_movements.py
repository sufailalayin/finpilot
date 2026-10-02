import inspect
from decimal import Decimal

from app.services.ai_context import _ai_account_movement, build_finance_context


def test_ai_account_movement_combines_all_money_sources():
    movement = _ai_account_movement(
        transaction_movement=Decimal("100.00"),
        receivable_movement=Decimal("-25.00"),
        liability_inflow=Decimal("400.00"),
        liability_outflow=Decimal("75.00"),
    )

    assert movement == Decimal("400.00")


def test_ai_account_movement_handles_receivable_inflow():
    movement = _ai_account_movement(
        transaction_movement=Decimal("0.00"),
        receivable_movement=Decimal("250.00"),
        liability_inflow=Decimal("0.00"),
        liability_outflow=Decimal("0.00"),
    )

    assert movement == Decimal("250.00")


def test_ai_account_balance_query_includes_receivable_and_liability_ledgers():
    source = inspect.getsource(build_finance_context)

    assert "ReceivableMovement.destination_account_id == account.id" in source
    assert "ReceivableMovement.source_account_id == account.id" in source
    assert "Liability.funding_account_id == account.id" in source
    assert "LiabilityPayment.payment_account_id == account.id" in source
    assert "total_movement = _ai_account_movement(" in source
