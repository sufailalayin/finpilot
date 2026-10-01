from datetime import date
from uuid import uuid4

import httpx
import pytest

from app.main import app


async def _register(client: httpx.AsyncClient, prefix: str) -> dict[str, str]:
    email = f"{prefix}-{uuid4().hex}@example.com"
    password = "StrongPass123!"
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Accuracy Test"},
    )
    assert register.status_code == 202, register.text
    verify = await client.post(
        "/api/v1/auth/register/verify",
        json={"email": email, "code": "123456"},
    )
    assert verify.status_code == 200, verify.text
    return {"Authorization": f"Bearer {verify.json()['access_token']}"}


@pytest.mark.asyncio
async def test_dashboard_preserves_decimals_excludes_cards_and_ignores_internal_transfers():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = await _register(client, "finance-accuracy")
        today = date.today().isoformat()

        bank = await client.post(
            "/api/v1/finance/accounts",
            headers=headers,
            json={
                "name": "Main Bank",
                "account_type": "bank",
                "currency": "INR",
                "opening_balance": "1000.25",
            },
        )
        assert bank.status_code == 201, bank.text
        bank_id = bank.json()["id"]

        second_bank = await client.post(
            "/api/v1/finance/accounts",
            headers=headers,
            json={
                "name": "Savings Bank",
                "account_type": "bank",
                "currency": "INR",
                "opening_balance": "0.00",
            },
        )
        assert second_bank.status_code == 201, second_bank.text
        second_bank_id = second_bank.json()["id"]

        card = await client.post(
            "/api/v1/finance/accounts",
            headers=headers,
            json={
                "name": "Credit Card",
                "account_type": "card",
                "currency": "INR",
                "opening_balance": "500.50",
                "credit_limit": "5000.00",
                "card_last4": "1234",
                "statement_day": 5,
                "payment_due_day": 25,
            },
        )
        assert card.status_code == 201, card.text

        for tx_type, amount, merchant in (
            ("income", "1000.50", "Salary"),
            ("expense", "100.25", "Groceries"),
        ):
            response = await client.post(
                "/api/v1/finance/transactions",
                headers=headers,
                json={
                    "account_id": bank_id,
                    "category_id": None,
                    "transaction_type": tx_type,
                    "amount": amount,
                    "occurred_on": today,
                    "merchant": merchant,
                    "note": "accuracy regression",
                },
            )
            assert response.status_code == 201, response.text

        transfer = await client.post(
            "/api/v1/finance/transfers",
            headers=headers,
            json={
                "from_account_id": bank_id,
                "to_account_id": second_bank_id,
                "amount": "200.10",
                "occurred_on": today,
                "note": "internal transfer",
            },
        )
        assert transfer.status_code == 201, transfer.text

        balances = await client.get("/api/v1/finance/accounts/balances", headers=headers)
        assert balances.status_code == 200, balances.text
        by_name = {row["name"]: row for row in balances.json()}
        assert by_name["Main Bank"]["current_balance"] == "1700.40"
        assert by_name["Savings Bank"]["current_balance"] == "200.10"
        assert by_name["Credit Card"]["current_balance"] == "500.50"

        dashboard = await client.get("/api/v1/dashboard", headers=headers)
        assert dashboard.status_code == 200, dashboard.text
        data = dashboard.json()
        assert data["summary"]["month_income"] == "1000.50"
        assert data["summary"]["month_expense"] == "100.25"
        assert data["summary"]["month_net"] == "900.25"
        assert data["summary"]["total_balance"] == "1900.50"
        assert data["savings_rate"] == 90.0
        assert data["liabilities"] == "500.50"
        assert data["net_worth"] == "1400.00"
        assert data["emergency_fund"]["liquid_balance"] == "1900.50"

        card_row = next(row for row in data["accounts"] if row["account_type"] == "card")
        assert card_row["balance"] == "500.50"


@pytest.mark.asyncio
async def test_health_score_waits_for_income_instead_of_rating_expense_only_data():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = await _register(client, "health-accuracy")
        today = date.today().isoformat()

        account = await client.post(
            "/api/v1/finance/accounts",
            headers=headers,
            json={
                "name": "Cash",
                "account_type": "cash",
                "currency": "INR",
                "opening_balance": "100.00",
            },
        )
        assert account.status_code == 201, account.text

        expense = await client.post(
            "/api/v1/finance/transactions",
            headers=headers,
            json={
                "account_id": account.json()["id"],
                "category_id": None,
                "transaction_type": "expense",
                "amount": "10.50",
                "occurred_on": today,
                "merchant": "Food",
                "note": None,
            },
        )
        assert expense.status_code == 201, expense.text

        dashboard = await client.get("/api/v1/dashboard", headers=headers)
        assert dashboard.status_code == 200, dashboard.text
        data = dashboard.json()
        assert data["health_score_available"] is False
        assert data["financial_health_score"] == 0
        assert data["health_grade"] == "Not enough data"

@pytest.mark.asyncio
async def test_internal_transfer_marker_survives_merchant_edit_and_real_transfer_label_counts():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = await _register(client, "transfer-marker")
        today = date.today().isoformat()

        main = await client.post(
            "/api/v1/finance/accounts",
            headers=headers,
            json={
                "name": "Main",
                "account_type": "bank",
                "currency": "INR",
                "opening_balance": "0.00",
            },
        )
        assert main.status_code == 201, main.text
        main_id = main.json()["id"]

        savings = await client.post(
            "/api/v1/finance/accounts",
            headers=headers,
            json={
                "name": "Savings",
                "account_type": "bank",
                "currency": "INR",
                "opening_balance": "0.00",
            },
        )
        assert savings.status_code == 201, savings.text
        savings_id = savings.json()["id"]

        income = await client.post(
            "/api/v1/finance/transactions",
            headers=headers,
            json={
                "account_id": main_id,
                "category_id": None,
                "transaction_type": "income",
                "amount": "1000.00",
                "occurred_on": today,
                "merchant": "Salary",
                "note": None,
            },
        )
        assert income.status_code == 201, income.text

        transfer = await client.post(
            "/api/v1/finance/transfers",
            headers=headers,
            json={
                "from_account_id": main_id,
                "to_account_id": savings_id,
                "amount": "250.00",
                "occurred_on": today,
                "note": "Move to savings",
            },
        )
        assert transfer.status_code == 201, transfer.text
        transfer_data = transfer.json()
        assert transfer_data["outgoing"]["is_internal_transfer"] is True
        assert transfer_data["incoming"]["is_internal_transfer"] is True

        outgoing_id = transfer_data["outgoing"]["id"]
        incoming_id = transfer_data["incoming"]["id"]

        edited = await client.patch(
            f"/api/v1/finance/transactions/{outgoing_id}",
            headers=headers,
            json={"merchant": "Edited transfer label"},
        )
        assert edited.status_code == 409, edited.text

        deleted = await client.delete(
            f"/api/v1/finance/transactions/{incoming_id}",
            headers=headers,
        )
        assert deleted.status_code == 409, deleted.text

        real_expense = await client.post(
            "/api/v1/finance/transactions",
            headers=headers,
            json={
                "account_id": main_id,
                "category_id": None,
                "transaction_type": "expense",
                "amount": "100.00",
                "occurred_on": today,
                "merchant": "Transfer out",
                "note": "Legitimate merchant text",
            },
        )
        assert real_expense.status_code == 201, real_expense.text
        assert real_expense.json()["is_internal_transfer"] is False

        dashboard = await client.get("/api/v1/dashboard", headers=headers)
        assert dashboard.status_code == 200, dashboard.text
        data = dashboard.json()

        assert data["summary"]["month_income"] == "1000.00"
        assert data["summary"]["month_expense"] == "100.00"
        assert data["summary"]["month_net"] == "900.00"
        assert data["savings_rate"] == 90.0

        balances = await client.get(
            "/api/v1/finance/accounts/balances",
            headers=headers,
        )
        assert balances.status_code == 200, balances.text
        by_name = {row["name"]: row for row in balances.json()}
        assert by_name["Main"]["current_balance"] == "650.00"
        assert by_name["Savings"]["current_balance"] == "250.00"

