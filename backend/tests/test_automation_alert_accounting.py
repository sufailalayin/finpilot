import inspect
from decimal import Decimal

from app.routers.automation import _automation_account_movement, smart_alerts


def test_automation_account_movement_matches_dashboard_signs():
    assert _automation_account_movement(
        Decimal("100.00"),
        Decimal("-25.00"),
        Decimal("400.00"),
        Decimal("75.00"),
    ) == Decimal("400.00")


def test_smart_alerts_fail_closed_on_unsupported_active_currency():
    source = inspect.getsource(smart_alerts)

    assert "await ensure_user_finance_currency(db, user.id)" in source


def test_spending_alert_metrics_ignore_internal_transfers_and_archived_accounts():
    source = inspect.getsource(smart_alerts)

    assert source.count("Transaction.is_internal_transfer.is_(False)") >= 4
    assert source.count("active_finance_account_ids(user.id)") >= 5


def test_cash_runway_excludes_cards_and_includes_all_account_movements():
    source = inspect.getsource(smart_alerts)

    assert 'if account.account_type.value == "card":' in source
    assert "continue" in source
    assert "ReceivableMovement.destination_account_id == account.id" in source
    assert "ReceivableMovement.source_account_id == account.id" in source
    assert "Liability.funding_account_id == account.id" in source
    assert "LiabilityPayment.payment_account_id == account.id" in source
    assert "total_movement = _automation_account_movement(" in source
