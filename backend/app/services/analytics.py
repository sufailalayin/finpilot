from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Category, Transaction, TransactionType
from app.models.planning import Budget


async def build_analytics(db: AsyncSession, user_id) -> dict:
    today = date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])

    summary_row = (
        await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Transaction.transaction_type
                                == TransactionType.INCOME,
                                Transaction.amount,
                            ),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("income"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Transaction.transaction_type
                                == TransactionType.EXPENSE,
                                Transaction.amount,
                            ),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("expenses"),
            ).where(
                Transaction.user_id == user_id,
                Transaction.occurred_on >= start,
                Transaction.occurred_on <= end,
            )
        )
    ).one()

    income = summary_row.income
    expenses = summary_row.expenses
    net = income - expenses
    savings_rate = float((net / income) * 100) if income > 0 else 0.0

    category_rows = (
        await db.execute(
            select(
                func.coalesce(Category.name, "Uncategorized").label("category"),
                func.sum(Transaction.amount).label("amount"),
            )
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.occurred_on >= start,
                Transaction.occurred_on <= end,
            )
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )
    ).all()

    top_categories = []
    for row in category_rows[:5]:
        pct = float((row.amount / expenses) * 100) if expenses > 0 else 0.0
        top_categories.append(
            {
                "category": row.category,
                "amount": row.amount,
                "percentage": round(pct, 1),
            }
        )

    budget_rows = (
        await db.execute(
            select(Budget)
            .where(
                Budget.user_id == user_id,
                Budget.period_start <= today,
                Budget.period_end >= today,
            )
            .order_by(Budget.created_at.desc())
        )
    ).scalars().all()

    budget_progress = []
    over_budget_count = 0

    for budget in budget_rows:
        conditions = [
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.occurred_on >= budget.period_start,
            Transaction.occurred_on <= budget.period_end,
        ]
        if budget.category_id is not None:
            conditions.append(Transaction.category_id == budget.category_id)

        spent = await db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
                *conditions
            )
        )
        spent = spent or Decimal("0.00")
        pct = float((spent / budget.amount) * 100) if budget.amount > 0 else 0.0

        if pct >= 100:
            status = "over"
            over_budget_count += 1
        elif pct >= 80:
            status = "warning"
        else:
            status = "good"

        budget_progress.append(
            {
                "name": budget.name,
                "spent": spent,
                "limit": budget.amount,
                "percentage": round(pct, 1),
                "status": status,
            }
        )

    score = 50
    if income > 0:
        if savings_rate >= 30:
            score += 25
        elif savings_rate >= 20:
            score += 20
        elif savings_rate >= 10:
            score += 12
        elif savings_rate > 0:
            score += 5
        else:
            score -= 15

        expense_ratio = float(expenses / income)
        if expense_ratio <= 0.6:
            score += 15
        elif expense_ratio <= 0.8:
            score += 8
        elif expense_ratio > 1:
            score -= 15

    score -= min(over_budget_count * 8, 24)
    score = max(0, min(100, score))

    insights = []

    if income <= 0 and expenses > 0:
        insights.append(
            {
                "title": "Add your income",
                "message": "Income is not recorded this month, so savings analysis is incomplete.",
                "severity": "warning",
            }
        )
    elif savings_rate >= 20:
        insights.append(
            {
                "title": "Strong savings rate",
                "message": f"You are saving about {savings_rate:.0f}% of recorded income this month.",
                "severity": "good",
            }
        )
    elif income > 0 and savings_rate < 10:
        insights.append(
            {
                "title": "Savings need attention",
                "message": f"Your current savings rate is about {savings_rate:.0f}%. Aim for at least 10–20% if practical.",
                "severity": "warning",
            }
        )

    if top_categories:
        top = top_categories[0]
        insights.append(
            {
                "title": "Top spending category",
                "message": f"{top['category']} accounts for {top['percentage']:.0f}% of this month's expenses.",
                "severity": "info",
            }
        )

    if over_budget_count:
        insights.append(
            {
                "title": "Budget exceeded",
                "message": f"{over_budget_count} active budget(s) have reached or exceeded their limits.",
                "severity": "warning",
            }
        )
    elif budget_rows:
        insights.append(
            {
                "title": "Budgets are under control",
                "message": "None of your active budgets are currently over their limits.",
                "severity": "good",
            }
        )

    if not insights:
        insights.append(
            {
                "title": "Keep tracking",
                "message": "Add more income and expense data to unlock deeper financial insights.",
                "severity": "info",
            }
        )

    return {
        "income": income,
        "expenses": expenses,
        "net": net,
        "savings_rate": round(savings_rate, 1),
        "financial_health_score": score,
        "top_categories": top_categories,
        "budgets": budget_progress,
        "insights": insights[:4],
    }



def _month_shift(year: int, month: int, offset: int) -> tuple[int, int]:
    absolute = year * 12 + (month - 1) + offset
    return absolute // 12, absolute % 12 + 1


async def build_report(db: AsyncSession, user_id, months: int = 6) -> dict:
    from app.models.finance import FinanceAccount

    today = date.today()
    months = max(2, min(months, 24))
    trend: list[dict] = []

    accounts = list(
        (
            await db.execute(
                select(FinanceAccount)
                .where(FinanceAccount.user_id == user_id)
                .order_by(FinanceAccount.created_at.asc())
            )
        ).scalars().all()
    )

    for offset in range(-(months - 1), 1):
        year, month = _month_shift(today.year, today.month, offset)
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])

        summary = (
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
                    ).label("expenses"),
                ).where(
                    Transaction.user_id == user_id,
                    Transaction.occurred_on >= start,
                    Transaction.occurred_on <= end,
                )
            )
        ).one()

        income = summary.income
        expenses = summary.expenses
        net = income - expenses
        savings_rate = float((net / income) * 100) if income > 0 else 0.0

        net_worth = Decimal("0.00")
        for account in accounts:
            if account.created_at.date() > end:
                continue
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
                    Transaction.occurred_on <= end,
                )
            )
            net_worth += account.opening_balance + (movement or Decimal("0.00"))

        trend.append(
            {
                "month": start.strftime("%Y-%m"),
                "income": income,
                "expenses": expenses,
                "net": net,
                "savings_rate": round(savings_rate, 1),
                "net_worth": net_worth,
            }
        )

    current = trend[-1]
    previous = trend[-2] if len(trend) >= 2 else None

    def change_pct(current_value, previous_value):
        if previous_value in (None, 0, Decimal("0.00")):
            return None
        return round(float((current_value - previous_value) / abs(previous_value) * 100), 1)

    current_year, current_month = today.year, today.month
    current_start = date(current_year, current_month, 1)
    current_end = date(current_year, current_month, monthrange(current_year, current_month)[1])

    category_rows = (
        await db.execute(
            select(
                func.coalesce(Category.name, "Uncategorized").label("category"),
                func.sum(Transaction.amount).label("amount"),
            )
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.occurred_on >= current_start,
                Transaction.occurred_on <= current_end,
            )
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )
    ).all()

    total_expenses = current["expenses"]
    categories = [
        {
            "category": row.category,
            "amount": row.amount,
            "percentage": round(float(row.amount / total_expenses * 100), 1)
            if total_expenses > 0
            else 0.0,
        }
        for row in category_rows
    ]

    return {
        "months": months,
        "current_month": current,
        "previous_month": previous,
        "income_change_pct": change_pct(
            current["income"], previous["income"] if previous else None
        ),
        "expense_change_pct": change_pct(
            current["expenses"], previous["expenses"] if previous else None
        ),
        "net_change_pct": change_pct(
            current["net"], previous["net"] if previous else None
        ),
        "trend": trend,
        "category_breakdown": categories,
    }
