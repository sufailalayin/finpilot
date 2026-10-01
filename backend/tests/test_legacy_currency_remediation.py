import inspect

import pytest
from pydantic import ValidationError

from app.routers.finance import net_worth_summary, remediate_account_currency, update_account, update_transaction
from app.routers.liabilities import debt_overview
from app.routers.planning import budget_dashboard
from app.schemas.finance import AccountCurrencyRemediation
from app.services.analytics import build_analytics, build_report
from app.services.dashboard import build_dashboard
from app.services.ai_context import build_finance_context


def _source(function) -> str:
    return inspect.getsource(function)


@pytest.mark.parametrize("mode", ["metadata_correction", "archive_legacy"])
def test_currency_remediation_contract_accepts_explicit_modes(mode):
    payload = AccountCurrencyRemediation(
        mode=mode,
        confirmation="REMEDIATE_LEGACY_CURRENCY",
    )
    assert payload.mode.value == mode


def test_currency_remediation_contract_requires_explicit_confirmation():
    with pytest.raises(ValidationError):
        AccountCurrencyRemediation(
            mode="archive_legacy",
            confirmation="yes",
        )


def test_currency_remediation_endpoint_distinguishes_safe_paths():
    source = _source(remediate_account_currency)
    assert "_account_historical_activity_count" in source
    assert "_account_archive_blocker_count" in source
    assert 'account.currency = "INR"' in source
    assert "account.is_archived = True" in source


@pytest.mark.parametrize(
    "function",
    [
        build_dashboard,
        build_analytics,
        build_report,
        budget_dashboard,
        debt_overview,
    ],
)
def test_transaction_aggregates_filter_archived_accounts(function):
    assert "active_finance_account_ids" in _source(function)


def test_net_worth_filters_archived_accounts():
    assert "FinanceAccount.is_archived.is_(False)" in _source(net_worth_summary)



def test_archived_account_update_is_read_only_except_name():
    source = _source(update_account)
    assert 'set(values) - {"name"}' in source
    assert "Archived legacy accounts are read-only" in source
    assert '"opening_balance" in values' in source
    assert "ensure_supported_account_currency" in source



def test_transaction_reassignment_validates_current_account_before_destination():
    source = _source(update_transaction)
    assert "current_account = await db.scalar" in source
    assert "FinanceAccount.id == transaction.account_id" in source
    assert "ensure_supported_account_currency(current_account)" in source


def test_ai_context_quarantines_archived_accounts():
    source = _source(build_finance_context)
    assert "ensure_user_finance_currency" in source
    assert source.count("active_finance_account_ids") >= 4
    assert "FinanceAccount.is_archived.is_(False)" in source
