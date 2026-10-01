import inspect

from app.routers.automation import create_recurring, overview, update_recurring


def test_recurring_create_enforces_supported_account_currency():
    source = inspect.getsource(create_recurring)

    assert "ensure_supported_account_currency(account)" in source


def test_recurring_account_change_and_reactivation_enforce_supported_currency():
    source = inspect.getsource(update_recurring)

    assert source.count("ensure_supported_account_currency(account)") >= 2
    assert 'values.get("is_active") is True' in source
    assert "FinanceAccount.id == rule.account_id" in source


def test_automation_overview_excludes_quarantined_recurring_rules():
    source = inspect.getsource(overview)

    assert ".join(FinanceAccount, FinanceAccount.id == RecurringRule.account_id)" in source
    assert "FinanceAccount.is_archived.is_(False)" in source
    assert 'func.upper(func.trim(FinanceAccount.currency)) == "INR"' in source
