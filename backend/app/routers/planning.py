import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.finance import Category, Transaction, TransactionType
from app.models.planning import Budget, SavingsGoal
from app.models.user import User
from app.schemas.planning import (
    BudgetCreate,
    BudgetResponse,
    BudgetDashboard,
    BudgetPerformance,
    GoalContribution,
    GoalDashboard,
    GoalPlan,
    SavingsGoalCreate,
    SavingsGoalResponse,
)

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    payload: BudgetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BudgetResponse:
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="period_end must be on or after period_start")

    if payload.category_id is not None:
        category = await db.scalar(
            select(Category).where(Category.id == payload.category_id, Category.user_id == user.id)
        )
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")

    budget = Budget(user_id=user.id, **payload.model_dump())
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return BudgetResponse.model_validate(budget)


@router.get("/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BudgetResponse]:
    result = await db.execute(
        select(Budget).where(Budget.user_id == user.id).order_by(Budget.period_start.desc())
    )
    return [BudgetResponse.model_validate(row) for row in result.scalars().all()]


@router.post("/goals", response_model=SavingsGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: SavingsGoalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavingsGoalResponse:
    if payload.current_amount > payload.target_amount:
        raise HTTPException(status_code=400, detail="current_amount cannot exceed target_amount")

    goal = SavingsGoal(user_id=user.id, **payload.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return SavingsGoalResponse.model_validate(goal)


@router.get("/goals", response_model=list[SavingsGoalResponse])
async def list_goals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavingsGoalResponse]:
    result = await db.execute(
        select(SavingsGoal).where(SavingsGoal.user_id == user.id).order_by(SavingsGoal.created_at.desc())
    )
    return [SavingsGoalResponse.model_validate(row) for row in result.scalars().all()]


@router.post("/goals/{goal_id}/contribute", response_model=SavingsGoalResponse)
async def contribute_to_goal(
    goal_id: uuid.UUID,
    payload: GoalContribution,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavingsGoalResponse:
    goal = await db.scalar(
        select(SavingsGoal).where(SavingsGoal.id == goal_id, SavingsGoal.user_id == user.id)
    )
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    goal.current_amount = min(goal.target_amount, goal.current_amount + payload.amount)
    await db.commit()
    await db.refresh(goal)
    return SavingsGoalResponse.model_validate(goal)


@router.get("/budgets/dashboard", response_model=BudgetDashboard)
async def budget_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BudgetDashboard:
    today = date.today()
    budgets = list((await db.execute(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.period_start <= today,
            Budget.period_end >= today,
        ).order_by(Budget.amount.desc())
    )).scalars().all())

    rows = []
    total_budget = Decimal("0.00")
    total_spent = Decimal("0.00")
    projected_total = Decimal("0.00")

    for budget in budgets:
        filters = [
            Transaction.user_id == user.id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.occurred_on >= budget.period_start,
            Transaction.occurred_on <= min(today, budget.period_end),
        ]
        if budget.category_id is not None:
            filters.append(Transaction.category_id == budget.category_id)

        spent = await db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(*filters)
        )
        spent = spent or Decimal("0.00")
        total_days = max((budget.period_end - budget.period_start).days + 1, 1)
        elapsed_days = max((min(today, budget.period_end) - budget.period_start).days + 1, 1)
        projected = (spent / Decimal(elapsed_days)) * Decimal(total_days)
        remaining = budget.amount - spent
        overrun = max(Decimal("0.00"), projected - budget.amount)
        usage = float(spent / budget.amount * 100) if budget.amount > 0 else 0.0

        if spent > budget.amount:
            state = "over"
        elif usage >= float(budget.alert_threshold_pct):
            state = "warning"
        elif projected > budget.amount:
            state = "forecast_over"
        else:
            state = "on_track"

        rows.append(BudgetPerformance(
            id=budget.id,
            name=budget.name,
            budget_amount=budget.amount,
            spent=spent,
            remaining=remaining,
            usage_pct=round(usage, 1),
            projected_spend=projected.quantize(Decimal("0.01")),
            projected_overrun=overrun.quantize(Decimal("0.01")),
            status=state,
            rollover_enabled=budget.rollover_enabled,
            alert_threshold_pct=budget.alert_threshold_pct,
            period_start=budget.period_start,
            period_end=budget.period_end,
            category_id=budget.category_id,
        ))
        total_budget += budget.amount
        total_spent += spent
        projected_total += projected

    return BudgetDashboard(
        total_budget=total_budget,
        total_spent=total_spent,
        total_remaining=total_budget - total_spent,
        projected_total_spend=projected_total.quantize(Decimal("0.01")),
        budgets=rows,
    )



@router.get("/goals/dashboard", response_model=GoalDashboard)
async def goal_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalDashboard:
    today = date.today()
    goals = list(
        (
            await db.execute(
                select(SavingsGoal)
                .where(SavingsGoal.user_id == user.id)
                .order_by(SavingsGoal.target_date.asc().nullslast(), SavingsGoal.created_at.desc())
            )
        ).scalars().all()
    )

    rows = []
    total_target = Decimal("0.00")
    total_saved = Decimal("0.00")

    for goal in goals:
        remaining = max(Decimal("0.00"), goal.target_amount - goal.current_amount)
        progress = float(goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0.0
        months_remaining = None
        required = None
        state = "on_track"

        if goal.current_amount >= goal.target_amount:
            state = "completed"
        elif goal.target_date is not None:
            if goal.target_date < today:
                state = "overdue"
                months_remaining = 0
            else:
                month_delta = (goal.target_date.year - today.year) * 12 + goal.target_date.month - today.month
                months_remaining = max(month_delta, 1)
                required = (remaining / Decimal(months_remaining)).quantize(Decimal("0.01"))
                if months_remaining <= 2 and progress < 75:
                    state = "needs_attention"

        rows.append(
            GoalPlan(
                id=goal.id,
                name=goal.name,
                goal_type=goal.goal_type,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                remaining_amount=remaining,
                progress_pct=round(progress, 1),
                target_date=goal.target_date,
                months_remaining=months_remaining,
                required_monthly_contribution=required,
                status=state,
            )
        )
        total_target += goal.target_amount
        total_saved += goal.current_amount

    return GoalDashboard(
        total_target=total_target,
        total_saved=total_saved,
        total_remaining=max(Decimal("0.00"), total_target - total_saved),
        goals=rows,
    )
