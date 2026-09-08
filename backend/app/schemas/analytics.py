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


class HealthScoreComponent(BaseModel):
    key: str
    label: str
    score: int
    max_score: int
    status: str
    message: str


class AnalyticsOverview(BaseModel):
    income: Decimal
    expenses: Decimal
    net: Decimal
    savings_rate: float
    financial_health_score: int
    health_grade: str
    health_components: list[HealthScoreComponent]
    top_categories: list[CategorySpend]
    budgets: list[BudgetProgress]
    insights: list[FinanceInsight]


class MonthlyTrendPoint(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal
    savings_rate: float
    net_worth: Decimal


class CategoryTrendPoint(BaseModel):
    category: str
    amount: Decimal
    percentage: float


class AnalyticsReport(BaseModel):
    months: int
    current_month: MonthlyTrendPoint
    previous_month: MonthlyTrendPoint | None = None
    income_change_pct: float | None = None
    expense_change_pct: float | None = None
    net_change_pct: float | None = None
    trend: list[MonthlyTrendPoint]
    category_breakdown: list[CategoryTrendPoint]
