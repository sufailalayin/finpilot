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
        return (
            f"This month you recorded ₹{month['income']} income and "
            f"₹{month['expense']} expenses, leaving a net of ₹{month['net']}. "
            f"{spending_line}{goal_line} "
            "Add more transactions and budgets for a more precise FinPilot analysis."
        )


class OpenAIProvider(AIProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        self.model_name = settings.openai_model

    async def answer(self, question: str, context: dict) -> str:
        instructions = (
            "You are FinPilot AI, a personal finance assistant by Hastron Ventures. "
            "Use only supplied finance context for claims about the user's money. "
            "Do not invent financial data. Be concise, practical, and non-judgmental. "
            "Do not present outcomes as guaranteed financial advice. "
            "If data is insufficient, say what is missing."
        )
        user_input = (
            "User question:\n" + question +
            "\n\nFinance context (JSON):\n" +
            json.dumps(context, ensure_ascii=False)
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
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
            response.raise_for_status()
            data = response.json()

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
