import inspect
from decimal import Decimal
from uuid import uuid4

from app.models.finance import AccountType, FinanceAccount
from app.services.ai_context import _ai_account_balance, build_finance_context


def _account(account_type: AccountType, opening_balance: str) -> FinanceAccount:
    return FinanceAccount(
        user_id=uuid4(),
        name="Test account",
        account_type=account_type,
        currency="INR",
        opening_balance=Decimal(opening_balance),
    )


def test_ai_account_balance_treats_non_card_as_asset():
    balance, is_card_liability = _ai_account_balance(
        _account(AccountType.BANK, "1000.00"),
        Decimal("250.00"),
    )

    assert balance == Decimal("1250.00")
    assert is_card_liability is False


def test_ai_account_balance_treats_card_as_liability():
    balance, is_card_liability = _ai_account_balance(
        _account(AccountType.CARD, "1000.00"),
        Decimal("250.00"),
    )

    assert balance == Decimal("750.00")
    assert is_card_liability is True


def test_ai_card_outstanding_cannot_go_below_zero():
    balance, is_card_liability = _ai_account_balance(
        _account(AccountType.CARD, "1000.00"),
        Decimal("1500.00"),
    )

    assert balance == Decimal("0.00")
    assert is_card_liability is True


def test_ai_wealth_summary_subtracts_card_liabilities():
    source = inspect.getsource(build_finance_context)

    assert "card_liabilities += current_balance" in source
    assert "account_total += current_balance" in source
    assert "total_liabilities = debt_total + card_liabilities" in source
    assert '"net_worth": str(account_total + asset_total - total_liabilities)' in source
