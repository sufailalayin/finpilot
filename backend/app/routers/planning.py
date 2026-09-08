import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.finance import Category
from app.models.planning import Budget, SavingsGoal
from app.models.user import User
from app.schemas.planning import (
    BudgetCreate,
    BudgetResponse,
    GoalContribution,
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
