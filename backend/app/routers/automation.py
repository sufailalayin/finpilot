import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.automation import BillReminder, RecurringRule
from app.models.finance import FinanceAccount
from app.models.user import User
from app.schemas.automation import (
    AutomationOverview,
    AlertOverview,
    SmartAlert,
    BillCreate,
    BillResponse,
    RecurringRuleCreate,
    RecurringRuleResponse,
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
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
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

    critical = sum(1 for alert in alerts if alert.severity == "critical")
    warning = sum(1 for alert in alerts if alert.severity == "warning")
    info = sum(1 for alert in alerts if alert.severity == "info")
    return AlertOverview(
        critical_count=critical,
        warning_count=warning,
        info_count=info,
        alerts=alerts,
    )
