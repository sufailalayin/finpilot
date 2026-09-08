from decimal import Decimal

from pydantic import BaseModel


class CategorySpend(BaseModel):
    category: str
    amount: Decimal
    percentage: float


class BudgetProgress(BaseModel):
    name: str
    spent: Decimal
    limit: Decimal
    percentage: float
    status: str


class FinanceInsight(BaseModel):
    title: str
    message: str
    severity: str


class AnalyticsOverview(BaseModel):
    income: Decimal
    expenses: Decimal
    net: Decimal
    savings_rate: float
    financial_health_score: int
    top_categories: list[CategorySpend]
    budgets: list[BudgetProgress]
    insights: list[FinanceInsight]
