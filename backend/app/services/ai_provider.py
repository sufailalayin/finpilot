import json

from app.core.config import get_settings

settings = get_settings()


class AIProvider:
    provider_name = "stub"
    model_name = "finpilot-local"

    async def answer(self, question: str, context: dict) -> str:
        month = context["month"]
        categories = context["top_expense_categories"]
        goals = context["goals"]

        if categories:
            top = categories[0]
            spending_line = (
                f"Your largest expense category this month is {top['name']} "
                f"at ₹{top['amount']}."
            )
        else:
            spending_line = "You do not have enough categorized expenses yet."

        goal_line = ""
        if goals:
            goal = goals[0]
            goal_line = (
                f" Your latest savings goal is {goal['name']}: "
                f"₹{goal['current_amount']} saved toward ₹{goal['target_amount']}."
            )

        return (
            f"This month you recorded ₹{month['income']} income and "
            f"₹{month['expense']} expenses, leaving a net of ₹{month['net']}. "
            f"{spending_line}{goal_line} "
            "Add more transactions and budgets for a more precise FinPilot analysis."
        )


def get_ai_provider() -> AIProvider:
    return AIProvider()
