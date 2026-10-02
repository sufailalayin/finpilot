import inspect

from app.routers.finance import _account_delete_blocker_count, delete_account


def test_account_delete_blocker_covers_all_linked_financial_data():
    source = inspect.getsource(_account_delete_blocker_count)

    assert "_account_historical_activity_count(" in source
    assert "RecurringRule.user_id == user_id" in source
    assert "RecurringRule.account_id == account_id" in source
    assert "BillReminder.user_id == user_id" in source
    assert "BillReminder.account_id == account_id" in source


def test_account_delete_uses_comprehensive_blocker():
    source = inspect.getsource(delete_account)

    assert "await _account_delete_blocker_count(" in source
    assert "linked financial history or automation" in source
    assert "select(func.count()).select_from(Transaction)" not in source
