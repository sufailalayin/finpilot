import asyncio
import json

import httpx

from app.core.config import get_settings

settings = get_settings()


class AIProvider:
    provider_name = "local"
    model_name = "finpilot-local"

    async def answer(self, question: str, context: dict) -> str:
        month = context["month"]
        categories = context["top_expense_categories"]
        goals = context["goals"]
        spending_line = (
            f"Your largest expense category this month is {categories[0]['name']} at ₹{categories[0]['amount']}."
            if categories else
            "You do not have enough categorized expenses yet."
        )
        goal_line = ""
        if goals:
            goal = goals[0]
            goal_line = (
                f" Your latest savings goal is {goal['name']}: "
                f"₹{goal['current_amount']} saved toward ₹{goal['target_amount']}."
            )
        health = context.get("financial_health", {})
        wealth = context.get("wealth_summary", {})
        debt = context.get("liabilities", [])
        debt_line = (
            f" You have ₹{wealth.get('liabilities', '0')} recorded liabilities."
            if debt else
            " You have no recorded liabilities."
        )
        return (
            f"This month you recorded ₹{month['income']} income and "
            f"₹{month['expense']} expenses, leaving a net of ₹{month['net']}. "
            f"Your estimated net worth is ₹{wealth.get('net_worth', '0')} and "
            f"your financial health score is {health.get('score', 0)}/100 "
            f"({health.get('grade', 'Not rated')}). "
            f"{spending_line}{goal_line}{debt_line} "
            "Use the recorded data as a guide and keep your balances, bills and goals updated."
        )


class OpenAIProvider(AIProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        self.model_name = settings.openai_model

    async def answer(self, question: str, context: dict) -> str:
        instructions = (
            "You are FinPilot AI, a personal finance assistant by Hastron Ventures. "
            "Use only supplied finance context for claims about the user's money. "
            "You can reason across cash flow, current balances, net worth, assets, liabilities, "
            "EMIs, budgets, goals, recurring commitments, bills, subscriptions, recent transactions "
            "and the financial-health components. "
            "When useful, show the calculation or assumptions behind an answer. "
            "Prioritize specific next actions, but do not invent financial data or guarantee outcomes. "
            "For affordability questions, compare the purchase with cash flow, bills, debt and goals. "
            "For debt questions, consider EMI load and outstanding principal. "
            "For savings questions, consider budget pressure, emergency buffer and target dates. "
            "Be concise, practical, non-judgmental and clear when data is insufficient."
        )
        user_input = (
            "User question:\n" + question +
            "\n\nFinance context (JSON):\n" +
            json.dumps(context, ensure_ascii=False)
        )
        last_error: Exception | None = None
        data = None
        async with httpx.AsyncClient(timeout=45.0) as client:
            for attempt in range(2):
                try:
                    response = await client.post(
                        "https://api.openai.com/v1/responses",
                        headers={
                            "Authorization": "Bearer " + settings.openai_api_key,
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model_name,
                            "instructions": instructions,
                            "input": user_input,
                            "max_output_tokens": 700,
                        },
                    )
                    if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                        await asyncio.sleep(1.0)
                        continue
                    response.raise_for_status()
                    data = response.json()
                    break
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                    last_error = exc
                    if attempt == 0:
                        await asyncio.sleep(1.0)
                        continue
                    raise RuntimeError("AI provider is temporarily unavailable") from exc

        if data is None:
            raise RuntimeError("AI provider returned no response") from last_error

        if isinstance(data.get("output_text"), str) and data["output_text"].strip():
            return data["output_text"].strip()

        chunks = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                text_value = content.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    chunks.append(text_value.strip())
        if not chunks:
            raise RuntimeError("OpenAI returned no text response")
        return "\n".join(chunks)


def get_ai_provider() -> AIProvider:
    return OpenAIProvider() if settings.openai_api_key else AIProvider()
