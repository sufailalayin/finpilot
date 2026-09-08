from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.automation import BillReminder
from app.models.finance import FinanceAccount, Transaction, TransactionType
from app.models.liability import Liability
from app.models.planning import Budget
from app.services.analytics import build_analytics


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

    analytics = await build_analytics(db, user_id)

    investment_assets = await db.scalar(
        select(func.coalesce(func.sum(Asset.current_value), Decimal("0.00"))).where(
            Asset.user_id == user_id
        )
    )
    investment_assets = investment_assets or Decimal("0.00")

    liabilities = await db.scalar(
        select(
            func.coalesce(
                func.sum(Liability.outstanding_principal),
                Decimal("0.00"),
            )
        ).where(Liability.user_id == user_id)
    )
    liabilities = liabilities or Decimal("0.00")
    net_worth = total_balance + investment_assets - liabilities

    active_budgets = list(
        (
            await db.execute(
                select(Budget).where(
                    Budget.user_id == user_id,
                    Budget.period_start <= today,
                    Budget.period_end >= today,
                )
            )
        ).scalars().all()
    )

    budget_warning_count = sum(
        1
        for item in analytics["budgets"]
        if item["status"] in {"warning", "over"}
    )

    bill_rows = list(
        (
            await db.execute(
                select(BillReminder)
                .where(
                    BillReminder.user_id == user_id,
                    BillReminder.is_paid.is_(False),
                    BillReminder.due_on >= today,
                )
                .order_by(BillReminder.due_on.asc())
                .limit(8)
            )
        ).scalars().all()
    )

    alerts = []
    for bill in bill_rows:
        days = (bill.due_on - today).days
        if days <= bill.reminder_days_before:
            alerts.append(
                {
                    "title": bill.name,
                    "message": (
                        "Due today"
                        if days == 0
                        else "Due in " + str(days) + " day(s)"
                    ),
                    "severity": "critical" if days == 0 else "warning",
                    "due_on": bill.due_on,
                }
            )

    insights = [
        {
            "title": "Health score",
            "value": str(analytics["financial_health_score"]) + "/100",
            "subtitle": analytics["health_grade"],
            "severity": (
                "good"
                if analytics["financial_health_score"] >= 70
                else "warning"
            ),
        },
        {
            "title": "Savings rate",
            "value": f'{analytics["savings_rate"]:.1f}%',
            "subtitle": "This month",
            "severity": (
                "good" if analytics["savings_rate"] >= 20 else "warning"
            ),
        },
        {
            "title": "Debt",
            "value": "₹" + format(liabilities, ",.0f"),
            "subtitle": "Outstanding liabilities",
            "severity": "warning" if liabilities > 0 else "good",
        },
        {
            "title": "Investments",
            "value": "₹" + format(investment_assets, ",.0f"),
            "subtitle": "Recorded asset value",
            "severity": "info",
        },
    ]

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
        "net_worth": net_worth,
        "investment_assets": investment_assets,
        "liabilities": liabilities,
        "savings_rate": analytics["savings_rate"],
        "financial_health_score": analytics["financial_health_score"],
        "health_grade": analytics["health_grade"],
        "active_budget_count": len(active_budgets),
        "budget_warning_count": budget_warning_count,
        "upcoming_alert_count": len(alerts),
        "insights": insights,
        "alerts": alerts,
    }
