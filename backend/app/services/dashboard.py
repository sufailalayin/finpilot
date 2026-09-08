from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FinanceAccount, Transaction, TransactionType


async def build_dashboard(db: AsyncSession, user_id) -> dict:
    today = date.today()
    period_start = today.replace(day=1)
    period_end = today.replace(day=monthrange(today.year, today.month)[1])

    month_rows = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("income"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.EXPENSE, Transaction.amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("expense"),
            func.count(Transaction.id).label("count"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.occurred_on >= period_start,
            Transaction.occurred_on <= period_end,
        )
    )
    month = month_rows.one()

    accounts_result = await db.execute(
        select(FinanceAccount)
        .where(FinanceAccount.user_id == user_id)
        .order_by(FinanceAccount.created_at.asc())
    )
    accounts = list(accounts_result.scalars().all())

    account_balances = []
    total_balance = Decimal("0.00")

    for account in accounts:
        totals_result = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("income"),
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.EXPENSE, Transaction.amount),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("expense"),
            ).where(
                Transaction.user_id == user_id,
                Transaction.account_id == account.id,
            )
        )
        totals = totals_result.one()
        balance = account.opening_balance + totals.income - totals.expense
        total_balance += balance
        account_balances.append(
            {
                "account_id": str(account.id),
                "account_name": account.name,
                "currency": account.currency,
                "balance": balance,
            }
        )

    recent_result = await db.execute(
        select(Transaction, FinanceAccount.name)
        .join(FinanceAccount, FinanceAccount.id == Transaction.account_id)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc())
        .limit(10)
    )

    recent = []
    for transaction, account_name in recent_result.all():
        recent.append(
            {
                "id": str(transaction.id),
                "account_name": account_name,
                "transaction_type": transaction.transaction_type.value,
                "amount": transaction.amount,
                "occurred_on": transaction.occurred_on,
                "merchant": transaction.merchant,
                "category_name": None,
            }
        )

    month_income = month.income
    month_expense = month.expense

    return {
        "summary": {
            "total_balance": total_balance,
            "month_income": month_income,
            "month_expense": month_expense,
            "month_net": month_income - month_expense,
            "transaction_count": month.count,
            "period_start": period_start,
            "period_end": period_end,
        },
        "accounts": account_balances,
        "recent_transactions": recent,
    }
