from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import BillReminder, RecurringRule
from app.models.asset import Asset
from app.models.finance import Category, FinanceAccount, Transaction, TransactionType
from app.models.liability import Liability
from app.models.planning import Budget, SavingsGoal
from app.services.analytics import build_analytics


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

    account_models = list(
        (
            await db.execute(
                select(FinanceAccount)
                .where(FinanceAccount.user_id == user_id)
                .order_by(FinanceAccount.created_at.asc())
            )
        ).scalars().all()
    )
    accounts = []
    for account in account_models:
        movement = await db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                            (Transaction.transaction_type == TransactionType.EXPENSE, -Transaction.amount),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                )
            ).where(
                Transaction.user_id == user_id,
                Transaction.account_id == account.id,
            )
        )
        accounts.append(
            {
                "name": account.name,
                "account_type": account.account_type.value,
                "current_balance": str(
                    account.opening_balance + (movement or Decimal("0.00"))
                ),
            }
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

    recurring = list(
        (
            await db.execute(
                select(
                    RecurringRule.name,
                    RecurringRule.transaction_type,
                    RecurringRule.amount,
                    RecurringRule.frequency,
                    RecurringRule.next_due_on,
                )
                .where(
                    RecurringRule.user_id == user_id,
                    RecurringRule.is_active.is_(True),
                )
                .order_by(RecurringRule.next_due_on.asc())
                .limit(20)
            )
        ).all()
    )

    bills = list(
        (
            await db.execute(
                select(
                    BillReminder.name,
                    BillReminder.amount,
                    BillReminder.due_on,
                    BillReminder.frequency,
                )
                .where(
                    BillReminder.user_id == user_id,
                    BillReminder.is_paid.is_(False),
                )
                .order_by(BillReminder.due_on.asc())
                .limit(20)
            )
        ).all()
    )

    liabilities = list(
        (
            await db.execute(
                select(
                    Liability.name,
                    Liability.liability_type,
                    Liability.outstanding_principal,
                    Liability.interest_rate,
                    Liability.emi_amount,
                    Liability.next_due_on,
                )
                .where(Liability.user_id == user_id)
                .order_by(Liability.outstanding_principal.desc())
                .limit(20)
            )
        ).all()
    )

    assets = list(
        (
            await db.execute(
                select(
                    Asset.name,
                    Asset.asset_type,
                    Asset.quantity,
                    Asset.cost_basis,
                    Asset.current_value,
                    Asset.maturity_date,
                )
                .where(Asset.user_id == user_id)
                .order_by(Asset.current_value.desc())
                .limit(30)
            )
        ).all()
    )

    recent_transactions = list(
        (
            await db.execute(
                select(
                    Transaction.transaction_type,
                    Transaction.amount,
                    Transaction.occurred_on,
                    Transaction.merchant,
                    Transaction.note,
                )
                .where(Transaction.user_id == user_id)
                .order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc())
                .limit(20)
            )
        ).all()
    )

    health = await build_analytics(db, user_id)
    account_total = sum(
        (Decimal(account["current_balance"]) for account in accounts),
        Decimal("0.00"),
    )
    asset_total = sum((row.current_value for row in assets), Decimal("0.00"))
    debt_total = sum(
        (row.outstanding_principal for row in liabilities),
        Decimal("0.00"),
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
        "accounts": accounts,
        "wealth_summary": {
            "liquid_accounts": str(account_total),
            "investment_assets": str(asset_total),
            "liabilities": str(debt_total),
            "net_worth": str(account_total + asset_total - debt_total),
        },
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
        "recurring_cash_flow": [
            {
                "name": name,
                "transaction_type": transaction_type,
                "amount": str(amount),
                "frequency": frequency,
                "next_due_on": str(next_due_on),
            }
            for name, transaction_type, amount, frequency, next_due_on in recurring
        ],
        "upcoming_bills": [
            {
                "name": name,
                "amount": str(amount),
                "due_on": str(due_on),
                "frequency": frequency,
            }
            for name, amount, due_on, frequency in bills
        ],
        "liabilities": [
            {
                "name": name,
                "liability_type": liability_type,
                "outstanding_principal": str(outstanding_principal),
                "interest_rate": str(interest_rate),
                "emi_amount": str(emi_amount),
                "next_due_on": str(next_due_on) if next_due_on else None,
            }
            for name, liability_type, outstanding_principal, interest_rate, emi_amount, next_due_on in liabilities
        ],
        "assets": [
            {
                "name": name,
                "asset_type": asset_type,
                "quantity": str(quantity),
                "cost_basis": str(cost_basis),
                "current_value": str(current_value),
                "maturity_date": str(maturity_date) if maturity_date else None,
            }
            for name, asset_type, quantity, cost_basis, current_value, maturity_date in assets
        ],
        "recent_transactions": [
            {
                "transaction_type": transaction_type.value,
                "amount": str(amount),
                "occurred_on": str(occurred_on),
                "merchant": merchant,
                "note": note,
            }
            for transaction_type, amount, occurred_on, merchant, note in recent_transactions
        ],
        "financial_health": {
            "score": health["financial_health_score"],
            "grade": health["health_grade"],
            "savings_rate": health["savings_rate"],
            "components": health["health_components"],
            "insights": health["insights"],
        },
    }
