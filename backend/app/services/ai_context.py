from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Category, FinanceAccount, Transaction, TransactionType
from app.models.planning import Budget, SavingsGoal


async def build_finance_context(db: AsyncSession, user_id) -> dict:
    today = date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])

    summary_row = (
        await db.execute(
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
                Transaction.occurred_on >= start,
                Transaction.occurred_on <= end,
            )
        )
    ).one()

    category_rows = await db.execute(
        select(
            Category.name,
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("amount"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.occurred_on >= start,
            Transaction.occurred_on <= end,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(8)
    )

    accounts = list(
        (
            await db.execute(
                select(FinanceAccount.name, FinanceAccount.opening_balance)
                .where(FinanceAccount.user_id == user_id)
                .order_by(FinanceAccount.created_at.asc())
            )
        ).all()
    )

    budgets = list(
        (
            await db.execute(
                select(Budget.name, Budget.amount, Budget.period_start, Budget.period_end)
                .where(Budget.user_id == user_id)
                .order_by(Budget.period_start.desc())
                .limit(10)
            )
        ).all()
    )

    goals = list(
        (
            await db.execute(
                select(
                    SavingsGoal.name,
                    SavingsGoal.current_amount,
                    SavingsGoal.target_amount,
                    SavingsGoal.target_date,
                )
                .where(SavingsGoal.user_id == user_id)
                .order_by(SavingsGoal.created_at.desc())
                .limit(10)
            )
        ).all()
    )

    return {
        "month": {
            "start": str(start),
            "end": str(end),
            "income": str(summary_row.income),
            "expense": str(summary_row.expense),
            "net": str(summary_row.income - summary_row.expense),
        },
        "top_expense_categories": [
            {"name": name, "amount": str(amount)}
            for name, amount in category_rows.all()
        ],
        "accounts": [
            {"name": name, "opening_balance": str(opening_balance)}
            for name, opening_balance in accounts
        ],
        "budgets": [
            {
                "name": name,
                "amount": str(amount),
                "period_start": str(period_start),
                "period_end": str(period_end),
            }
            for name, amount, period_start, period_end in budgets
        ],
        "goals": [
            {
                "name": name,
                "current_amount": str(current_amount),
                "target_amount": str(target_amount),
                "target_date": str(target_date) if target_date else None,
            }
            for name, current_amount, target_amount, target_date in goals
        ],
    }
