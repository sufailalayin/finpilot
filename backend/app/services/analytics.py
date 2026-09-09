from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.finance import Category, FinanceAccount, Transaction, TransactionType
from app.models.liability import Liability
from app.models.planning import Budget, SavingsGoal


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

    # A health score is only meaningful after the user records real
    # cash-flow activity. Without income/expense data, default component
    # points (for no debt, no budget overruns, etc.) can look like a real
    # score even though there is nothing to assess.
    health_score_available = income > 0 or expenses > 0

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

    account_rows = list(
        (
            await db.execute(
                select(FinanceAccount).where(FinanceAccount.user_id == user_id)
            )
        ).scalars().all()
    )
    liquid_assets = Decimal("0.00")
    for account in account_rows:
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
        liquid_assets += account.opening_balance + (movement or Decimal("0.00"))

    liabilities_total = await db.scalar(
        select(
            func.coalesce(
                func.sum(Liability.outstanding_principal),
                Decimal("0.00"),
            )
        ).where(Liability.user_id == user_id)
    )
    liabilities_total = liabilities_total or Decimal("0.00")

    monthly_emi = await db.scalar(
        select(
            func.coalesce(
                func.sum(Liability.emi_amount),
                Decimal("0.00"),
            )
        ).where(Liability.user_id == user_id)
    )
    monthly_emi = monthly_emi or Decimal("0.00")

    goal_rows = list(
        (
            await db.execute(
                select(SavingsGoal).where(SavingsGoal.user_id == user_id)
            )
        ).scalars().all()
    )
    goal_target = sum((g.target_amount for g in goal_rows), Decimal("0.00"))
    goal_saved = sum((g.current_amount for g in goal_rows), Decimal("0.00"))
    goal_progress = float(goal_saved / goal_target * 100) if goal_target > 0 else 0.0

    savings_score = 0
    if income > 0:
        if savings_rate >= 30:
            savings_score = 25
        elif savings_rate >= 20:
            savings_score = 21
        elif savings_rate >= 10:
            savings_score = 16
        elif savings_rate > 0:
            savings_score = 10
        else:
            savings_score = 2

    cashflow_score = 0
    if income > 0:
        expense_ratio = float(expenses / income)
        if expense_ratio <= 0.60:
            cashflow_score = 20
        elif expense_ratio <= 0.75:
            cashflow_score = 16
        elif expense_ratio <= 0.90:
            cashflow_score = 10
        elif expense_ratio <= 1.00:
            cashflow_score = 6
        else:
            cashflow_score = 1

    debt_score = 20
    dti = float(monthly_emi / income * 100) if income > 0 else None
    if liabilities_total > 0:
        if dti is None:
            debt_score = 8
        elif dti <= 20:
            debt_score = 20
        elif dti <= 35:
            debt_score = 15
        elif dti <= 50:
            debt_score = 9
        else:
            debt_score = 3

    budget_score = 15
    if budget_rows:
        over_count = sum(1 for row in budget_progress if row["status"] == "over")
        warning_count = sum(1 for row in budget_progress if row["status"] == "warning")
        budget_score = max(0, 15 - over_count * 6 - warning_count * 2)

    emergency_score = 0
    if expenses > 0:
        emergency_months = float(liquid_assets / expenses)
        if emergency_months >= 6:
            emergency_score = 10
        elif emergency_months >= 3:
            emergency_score = 8
        elif emergency_months >= 1:
            emergency_score = 5
        elif emergency_months > 0:
            emergency_score = 2
    elif liquid_assets > 0:
        emergency_score = 10

    goal_score = 0
    if not goal_rows:
        goal_score = 5
    elif goal_progress >= 75:
        goal_score = 10
    elif goal_progress >= 50:
        goal_score = 8
    elif goal_progress >= 25:
        goal_score = 6
    elif goal_progress > 0:
        goal_score = 4
    else:
        goal_score = 2

    score = max(
        0,
        min(
            100,
            savings_score
            + cashflow_score
            + debt_score
            + budget_score
            + emergency_score
            + goal_score,
        ),
    )

    if not health_score_available:
        score = 0

    health_grade = (
        "Not enough data"
        if not health_score_available
        else "Excellent"
        if score >= 85
        else "Strong"
        if score >= 70
        else "Fair"
        if score >= 55
        else "Needs attention"
        if score >= 40
        else "High risk"
    )

    def component_status(value: int, maximum: int) -> str:
        ratio = value / maximum if maximum else 0
        return "good" if ratio >= 0.75 else "warning" if ratio >= 0.45 else "critical"

    health_components = [
        {
            "key": "savings",
            "label": "Savings",
            "score": savings_score,
            "max_score": 25,
            "status": component_status(savings_score, 25),
            "message": f"Savings rate is {savings_rate:.1f}%.",
        },
        {
            "key": "cashflow",
            "label": "Cash flow",
            "score": cashflow_score,
            "max_score": 20,
            "status": component_status(cashflow_score, 20),
            "message": "Compares monthly spending with recorded income.",
        },
        {
            "key": "debt",
            "label": "Debt load",
            "score": debt_score,
            "max_score": 20,
            "status": component_status(debt_score, 20),
            "message": (
                f"EMI-to-income is {dti:.1f}%."
                if dti is not None
                else "Add income to calculate debt-to-income."
            ),
        },
        {
            "key": "budget",
            "label": "Budget discipline",
            "score": budget_score,
            "max_score": 15,
            "status": component_status(budget_score, 15),
            "message": "Based on active budget usage and overruns.",
        },
        {
            "key": "emergency",
            "label": "Emergency buffer",
            "score": emergency_score,
            "max_score": 10,
            "status": component_status(emergency_score, 10),
            "message": "Uses liquid account balances relative to monthly expenses.",
        },
        {
            "key": "goals",
            "label": "Goal progress",
            "score": goal_score,
            "max_score": 10,
            "status": component_status(goal_score, 10),
            "message": (
                f"Overall goal progress is {goal_progress:.1f}%."
                if goal_rows
                else "No savings goals created yet."
            ),
        },
    ]

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
        "health_score_available": health_score_available,
        "health_grade": health_grade,
        "health_components": health_components,
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

        debt = await db.scalar(
            select(
                func.coalesce(
                    func.sum(Liability.outstanding_principal),
                    Decimal("0.00"),
                )
            ).where(
                Liability.user_id == user_id,
                Liability.created_at <= end,
            )
        )
        debt = debt or Decimal("0.00")

        asset_value = await db.scalar(
            select(
                func.coalesce(
                    func.sum(Asset.current_value),
                    Decimal("0.00"),
                )
            ).where(
                Asset.user_id == user_id,
                Asset.created_at <= end,
            )
        )
        asset_value = asset_value or Decimal("0.00")

        trend.append(
            {
                "month": start.strftime("%Y-%m"),
                "income": income,
                "expenses": expenses,
                "net": net,
                "savings_rate": round(savings_rate, 1),
                "net_worth": net_worth + asset_value - debt,
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
