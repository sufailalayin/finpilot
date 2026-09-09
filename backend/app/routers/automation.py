import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.entitlements import require_pro_user
from app.models.automation import BillReminder, RecurringRule
from app.models.finance import FinanceAccount, Transaction, TransactionType
from app.models.liability import Liability
from app.models.planning import Budget, SavingsGoal
from app.models.user import User
from app.schemas.automation import (
    AutomationOverview,
    AlertOverview,
    SmartAlert,
    BillCreate,
    BillResponse,
    BillUpdate,
    CreditCardStatementCreate,
    RecurringRuleCreate,
    RecurringRuleResponse,
    RecurringRuleUpdate,
)

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post("/recurring", response_model=RecurringRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring(
    payload: RecurringRuleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecurringRuleResponse:
    account = await db.scalar(
        select(FinanceAccount).where(
            FinanceAccount.id == payload.account_id,
            FinanceAccount.user_id == user.id,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    if payload.transaction_type not in {"income", "expense"}:
        raise HTTPException(status_code=400, detail="transaction_type must be income or expense")
    if payload.frequency not in {"weekly", "monthly", "yearly"}:
        raise HTTPException(status_code=400, detail="Unsupported recurring frequency")

    rule = RecurringRule(user_id=user.id, **payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return RecurringRuleResponse.model_validate(rule)


@router.patch("/recurring/{rule_id}", response_model=RecurringRuleResponse)
async def update_recurring(
    rule_id: uuid.UUID,
    payload: RecurringRuleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecurringRuleResponse:
    rule = await db.scalar(
        select(RecurringRule).where(
            RecurringRule.id == rule_id,
            RecurringRule.user_id == user.id,
        )
    )
    if rule is None:
        raise HTTPException(status_code=404, detail="Recurring rule not found")

    values = payload.model_dump(exclude_unset=True)
    if "account_id" in values and values["account_id"] is not None:
        account = await db.scalar(
            select(FinanceAccount).where(
                FinanceAccount.id == values["account_id"],
                FinanceAccount.user_id == user.id,
            )
        )
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

    tx_type = values.get("transaction_type", rule.transaction_type)
    if tx_type not in {"income", "expense"}:
        raise HTTPException(status_code=400, detail="transaction_type must be income or expense")
    frequency = values.get("frequency", rule.frequency)
    if frequency not in {"weekly", "monthly", "yearly"}:
        raise HTTPException(status_code=400, detail="Unsupported recurring frequency")

    for field, value in values.items():
        if field == "name" and value is not None:
            value = value.strip()
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)
    return RecurringRuleResponse.model_validate(rule)


@router.delete("/recurring/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring(
    rule_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    rule = await db.scalar(
        select(RecurringRule).where(
            RecurringRule.id == rule_id,
            RecurringRule.user_id == user.id,
        )
    )
    if rule is None:
        raise HTTPException(status_code=404, detail="Recurring rule not found")
    await db.delete(rule)
    await db.commit()


@router.get("/recurring", response_model=list[RecurringRuleResponse])
async def list_recurring(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecurringRuleResponse]:
    result = await db.execute(
        select(RecurringRule)
        .where(RecurringRule.user_id == user.id)
        .order_by(RecurringRule.next_due_on.asc())
    )
    return [RecurringRuleResponse.model_validate(row) for row in result.scalars().all()]


@router.get("/cards/{account_id}/statements", response_model=list[BillResponse])
async def list_credit_card_statements(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BillResponse]:
    account = await db.scalar(
        select(FinanceAccount).where(
            FinanceAccount.id == account_id,
            FinanceAccount.user_id == user.id,
        )
    )
    if account is None or account.account_type.value != "card":
        raise HTTPException(status_code=404, detail="Credit card account not found")

    rows = list(
        (
            await db.execute(
                select(BillReminder)
                .where(
                    BillReminder.user_id == user.id,
                    BillReminder.account_id == account.id,
                    BillReminder.bill_type == "credit_card",
                )
                .order_by(
                    BillReminder.bill_generated_on.desc().nullslast(),
                    BillReminder.created_at.desc(),
                )
            )
        ).scalars().all()
    )
    return [BillResponse.model_validate(row) for row in rows]


@router.post("/cards/statements", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
async def create_credit_card_statement(
    payload: CreditCardStatementCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    account = await db.scalar(
        select(FinanceAccount).where(
            FinanceAccount.id == payload.account_id,
            FinanceAccount.user_id == user.id,
        )
    )
    if account is None or account.account_type.value != "card":
        raise HTTPException(status_code=404, detail="Credit card account not found")
    if payload.minimum_due is not None and payload.minimum_due > payload.amount:
        raise HTTPException(status_code=400, detail="Minimum due cannot exceed total due")

    bill = BillReminder(
        user_id=user.id,
        name=account.name + " statement",
        bill_type="credit_card",
        provider=account.name,
        account_id=account.id,
        amount=payload.amount,
        minimum_due=payload.minimum_due,
        paid_amount=Decimal("0.00"),
        due_on=payload.due_on,
        bill_generated_on=payload.generated_on,
        card_last4=account.card_last4,
        frequency="once",
        reminder_days_before=payload.reminder_days_before,
        auto_renew=False,
    )
    db.add(bill)
    await db.commit()
    await db.refresh(bill)
    return BillResponse.model_validate(bill)


@router.post("/bills", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
async def create_bill(
    payload: BillCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    if payload.frequency not in {"once", "weekly", "monthly", "yearly"}:
        raise HTTPException(status_code=400, detail="Unsupported bill frequency")
    bill = BillReminder(user_id=user.id, **payload.model_dump())
    db.add(bill)
    await db.commit()
    await db.refresh(bill)
    return BillResponse.model_validate(bill)


@router.patch("/bills/{bill_id}", response_model=BillResponse)
async def update_bill(
    bill_id: uuid.UUID,
    payload: BillUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    bill = await db.scalar(
        select(BillReminder).where(
            BillReminder.id == bill_id,
            BillReminder.user_id == user.id,
        )
    )
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")

    values = payload.model_dump(exclude_unset=True)
    frequency = values.get("frequency", bill.frequency)
    if frequency not in {"once", "weekly", "monthly", "yearly"}:
        raise HTTPException(status_code=400, detail="Unsupported bill frequency")

    for field, value in values.items():
        if field in {"name", "provider"} and value is not None:
            value = value.strip()
        setattr(bill, field, value)

    await db.commit()
    await db.refresh(bill)
    return BillResponse.model_validate(bill)


@router.delete("/bills/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bill(
    bill_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    bill = await db.scalar(
        select(BillReminder).where(
            BillReminder.id == bill_id,
            BillReminder.user_id == user.id,
        )
    )
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    await db.delete(bill)
    await db.commit()


@router.get("/bills", response_model=list[BillResponse])
async def list_bills(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BillResponse]:
    result = await db.execute(
        select(BillReminder)
        .where(BillReminder.user_id == user.id, BillReminder.is_paid.is_(False))
        .order_by(BillReminder.due_on.asc())
    )
    return [BillResponse.model_validate(row) for row in result.scalars().all()]


@router.post("/bills/{bill_id}/paid", response_model=BillResponse)
async def mark_bill_paid(
    bill_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    bill = await db.scalar(
        select(BillReminder).where(
            BillReminder.id == bill_id,
            BillReminder.user_id == user.id,
        )
    )
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    bill.is_paid = True
    await db.commit()
    await db.refresh(bill)
    return BillResponse.model_validate(bill)


def _occurrences_within_30d(rule: RecurringRule, today: date) -> int:
    end = today + timedelta(days=30)
    if not rule.is_active or rule.next_due_on > end:
        return 0
    if rule.frequency == "weekly":
        return ((end - max(today, rule.next_due_on)).days // 7) + 1
    return 1


@router.get("/overview", response_model=AutomationOverview)
async def overview(
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> AutomationOverview:
    today = date.today()
    end = today + timedelta(days=30)

    rules = list(
        (
            await db.execute(
                select(RecurringRule)
                .where(RecurringRule.user_id == user.id, RecurringRule.is_active.is_(True))
                .order_by(RecurringRule.next_due_on.asc())
            )
        ).scalars().all()
    )
    bills = list(
        (
            await db.execute(
                select(BillReminder)
                .where(
                    BillReminder.user_id == user.id,
                    BillReminder.is_paid.is_(False),
                    BillReminder.due_on >= today,
                    BillReminder.due_on <= end,
                )
                .order_by(BillReminder.due_on.asc())
            )
        ).scalars().all()
    )

    recurring_income = Decimal("0.00")
    recurring_expense = Decimal("0.00")
    for rule in rules:
        occurrences = _occurrences_within_30d(rule, today)
        value = rule.amount * occurrences
        if rule.transaction_type == "income":
            recurring_income += value
        elif rule.transaction_type == "expense":
            recurring_expense += value

    upcoming_bills = sum((bill.amount for bill in bills), Decimal("0.00"))
    projected = recurring_income - recurring_expense - upcoming_bills

    return AutomationOverview(
        recurring_income_30d=recurring_income,
        recurring_expense_30d=recurring_expense,
        upcoming_bills_30d=upcoming_bills,
        projected_30d_net=projected,
        recurring_rules=[RecurringRuleResponse.model_validate(row) for row in rules],
        bills=[BillResponse.model_validate(row) for row in bills],
    )



@router.get("/alerts", response_model=AlertOverview)
async def smart_alerts(
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOverview:
    today = date.today()
    horizon = today + timedelta(days=30)
    bills = list(
        (
            await db.execute(
                select(BillReminder)
                .where(
                    BillReminder.user_id == user.id,
                    BillReminder.is_paid.is_(False),
                    BillReminder.due_on <= horizon,
                )
                .order_by(BillReminder.due_on.asc())
            )
        ).scalars().all()
    )

    alerts: list[SmartAlert] = []
    for bill in bills:
        days = (bill.due_on - today).days
        reminder_window = bill.reminder_days_before

        if days < 0:
            alerts.append(
                SmartAlert(
                    alert_type="overdue_bill",
                    severity="critical",
                    title=bill.name + " is overdue",
                    message="Payment was due " + str(abs(days)) + " day(s) ago.",
                    due_on=bill.due_on,
                    amount=bill.amount,
                    source_id=bill.id,
                )
            )
        elif days <= reminder_window:
            alerts.append(
                SmartAlert(
                    alert_type="bill_due",
                    severity="warning" if days > 0 else "critical",
                    title=bill.name + (" is due today" if days == 0 else " is due soon"),
                    message=(
                        ("Due today." if days == 0 else "Due in " + str(days) + " day(s).")
                        + (" Auto-renew is enabled." if bill.auto_renew else "")
                    ),
                    due_on=bill.due_on,
                    amount=bill.amount,
                    source_id=bill.id,
                )
            )
        elif bill.bill_type == "subscription" and bill.auto_renew and days <= 7:
            alerts.append(
                SmartAlert(
                    alert_type="subscription_renewal",
                    severity="info",
                    title=bill.name + " renews soon",
                    message="Subscription renewal is scheduled in " + str(days) + " day(s).",
                    due_on=bill.due_on,
                    amount=bill.amount,
                    source_id=bill.id,
                )
            )

    liabilities = list(
        (
            await db.execute(
                select(Liability).where(
                    Liability.user_id == user.id,
                    Liability.next_due_on.is_not(None),
                    Liability.outstanding_principal > 0,
                )
            )
        ).scalars().all()
    )
    for liability in liabilities:
        if liability.next_due_on is None:
            continue
        days = (liability.next_due_on - today).days
        if 0 <= days <= 5:
            alerts.append(
                SmartAlert(
                    alert_type="emi_due",
                    severity="warning" if days > 0 else "critical",
                    title=liability.name + (" EMI due today" if days == 0 else " EMI due soon"),
                    message=(
                        "EMI of ₹" + format(liability.emi_amount, ",.0f")
                        + (" is due today." if days == 0 else " is due in " + str(days) + " day(s).")
                    ),
                    due_on=liability.next_due_on,
                    amount=liability.emi_amount,
                    source_id=liability.id,
                )
            )

    budgets = list(
        (
            await db.execute(
                select(Budget).where(
                    Budget.user_id == user.id,
                    Budget.period_start <= today,
                    Budget.period_end >= today,
                )
            )
        ).scalars().all()
    )
    for budget in budgets:
        filters = [
            Transaction.user_id == user.id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.occurred_on >= budget.period_start,
            Transaction.occurred_on <= today,
        ]
        if budget.category_id is not None:
            filters.append(Transaction.category_id == budget.category_id)
        spent = await db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(*filters)
        )
        spent = spent or Decimal("0.00")
        usage = float(spent / budget.amount * 100) if budget.amount > 0 else 0.0
        total_days = max((budget.period_end - budget.period_start).days + 1, 1)
        elapsed = max((today - budget.period_start).days + 1, 1)
        projected = spent / Decimal(elapsed) * Decimal(total_days)

        if spent > budget.amount:
            alerts.append(
                SmartAlert(
                    alert_type="budget_over",
                    severity="critical",
                    title=budget.name + " is over budget",
                    message="Spent ₹" + format(spent, ",.0f") + " against ₹" + format(budget.amount, ",.0f") + ".",
                    amount=spent,
                    source_id=budget.id,
                )
            )
        elif usage >= float(budget.alert_threshold_pct):
            alerts.append(
                SmartAlert(
                    alert_type="budget_warning",
                    severity="warning",
                    title=budget.name + " is near its limit",
                    message=f"{usage:.0f}% of the budget has been used.",
                    amount=spent,
                    source_id=budget.id,
                )
            )
        elif projected > budget.amount:
            alerts.append(
                SmartAlert(
                    alert_type="budget_forecast",
                    severity="warning",
                    title=budget.name + " may exceed its limit",
                    message="Projected spend is ₹" + format(projected, ",.0f") + ".",
                    amount=projected,
                    source_id=budget.id,
                )
            )

    goals = list(
        (
            await db.execute(
                select(SavingsGoal).where(
                    SavingsGoal.user_id == user.id,
                    SavingsGoal.target_date.is_not(None),
                    SavingsGoal.current_amount < SavingsGoal.target_amount,
                )
            )
        ).scalars().all()
    )
    for goal in goals:
        if goal.target_date is None:
            continue
        days = (goal.target_date - today).days
        progress = float(goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0.0
        if days < 0:
            alerts.append(
                SmartAlert(
                    alert_type="goal_overdue",
                    severity="warning",
                    title=goal.name + " target date has passed",
                    message=f"Goal is {progress:.0f}% complete.",
                    due_on=goal.target_date,
                    source_id=goal.id,
                )
            )
        elif days <= 60 and progress < 75:
            alerts.append(
                SmartAlert(
                    alert_type="goal_risk",
                    severity="info",
                    title=goal.name + " needs attention",
                    message=f"{progress:.0f}% complete with {days} day(s) remaining.",
                    due_on=goal.target_date,
                    source_id=goal.id,
                )
            )

    month_start = today.replace(day=1)
    month_expense = await db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.occurred_on >= month_start,
            Transaction.occurred_on <= today,
        )
    )
    month_expense = month_expense or Decimal("0.00")
    elapsed_days = max((today - month_start).days + 1, 1)
    avg_daily_expense = month_expense / Decimal(elapsed_days) if month_expense > 0 else Decimal("0.00")

    accounts = list(
        (
            await db.execute(
                select(FinanceAccount).where(FinanceAccount.user_id == user.id)
            )
        ).scalars().all()
    )
    total_liquid = Decimal("0.00")
    for account in accounts:
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
                Transaction.user_id == user.id,
                Transaction.account_id == account.id,
            )
        )
        total_liquid += account.opening_balance + (movement or Decimal("0.00"))

    if avg_daily_expense > 0:
        runway_days = float(total_liquid / avg_daily_expense)
        if runway_days < 7:
            alerts.append(
                SmartAlert(
                    alert_type="low_cash_runway",
                    severity="critical" if runway_days < 3 else "warning",
                    title="Low cash runway",
                    message=f"Recorded liquid balances cover about {runway_days:.1f} day(s) of current spending.",
                    amount=total_liquid,
                )
            )

    average_transaction = await db.scalar(
        select(func.avg(Transaction.amount)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.occurred_on >= month_start,
            Transaction.occurred_on <= today,
        )
    )
    if average_transaction is not None and average_transaction > 0:
        recent_large = list(
            (
                await db.execute(
                    select(Transaction)
                    .where(
                        Transaction.user_id == user.id,
                        Transaction.transaction_type == TransactionType.EXPENSE,
                        Transaction.occurred_on >= today - timedelta(days=3),
                        Transaction.amount >= Decimal(str(average_transaction)) * Decimal("2.5"),
                    )
                    .order_by(Transaction.amount.desc())
                    .limit(3)
                )
            ).scalars().all()
        )
        for transaction in recent_large:
            alerts.append(
                SmartAlert(
                    alert_type="large_expense",
                    severity="info",
                    title="Large expense detected",
                    message=(transaction.merchant or "Expense") + " was significantly above your recent average.",
                    due_on=transaction.occurred_on,
                    amount=transaction.amount,
                    source_id=transaction.id,
                )
            )

    alerts.sort(
        key=lambda item: (
            0 if item.severity == "critical" else 1 if item.severity == "warning" else 2,
            item.due_on or horizon,
        )
    )

    critical = sum(1 for alert in alerts if alert.severity == "critical")
    warning = sum(1 for alert in alerts if alert.severity == "warning")
    info = sum(1 for alert in alerts if alert.severity == "info")
    return AlertOverview(
        critical_count=critical,
        warning_count=warning,
        info_count=info,
        alerts=alerts,
    )
