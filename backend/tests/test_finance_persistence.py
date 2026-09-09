from uuid import uuid4

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_finance_values_persist_recalculate_and_reload():
    email = f"persistence-{uuid4().hex}@example.com"
    password = "StrongPass123!"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Persistence Test",
            },
        )
        assert register.status_code == 201, register.text
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        account = await client.post(
            "/api/v1/finance/accounts",
            headers=headers,
            json={
                "name": "Main Bank",
                "account_type": "bank",
                "currency": "INR",
                "opening_balance": "10000.00",
            },
        )
        assert account.status_code == 201, account.text
        account_id = account.json()["id"]

        balances = await client.get(
            "/api/v1/finance/accounts/balances",
            headers=headers,
        )
        assert balances.status_code == 200, balances.text
        assert balances.json()[0]["current_balance"] == "10000.00"

        income = await client.post(
            "/api/v1/finance/transactions",
            headers=headers,
            json={
                "account_id": account_id,
                "category_id": None,
                "transaction_type": "income",
                "amount": "2500.00",
                "occurred_on": "2026-09-09",
                "merchant": "Test income",
                "note": "Persistence regression",
            },
        )
        assert income.status_code == 201, income.text
        transaction_id = income.json()["id"]

        balances = await client.get(
            "/api/v1/finance/accounts/balances",
            headers=headers,
        )
        assert balances.status_code == 200, balances.text
        assert balances.json()[0]["current_balance"] == "12500.00"

        update_tx = await client.patch(
            f"/api/v1/finance/transactions/{transaction_id}",
            headers=headers,
            json={
                "amount": "4000.00",
                "merchant": "Updated income",
            },
        )
        assert update_tx.status_code == 200, update_tx.text
        assert update_tx.json()["amount"] == "4000.00"

        transactions = await client.get(
            "/api/v1/finance/transactions",
            headers=headers,
        )
        assert transactions.status_code == 200, transactions.text
        stored = next(
            item for item in transactions.json()
            if item["id"] == transaction_id
        )
        assert stored["amount"] == "4000.00"
        assert stored["merchant"] == "Updated income"

        balances = await client.get(
            "/api/v1/finance/accounts/balances",
            headers=headers,
        )
        assert balances.json()[0]["current_balance"] == "14000.00"

        update_account = await client.patch(
            f"/api/v1/finance/accounts/{account_id}",
            headers=headers,
            json={"opening_balance": "15000.00"},
        )
        assert update_account.status_code == 200, update_account.text

        balances = await client.get(
            "/api/v1/finance/accounts/balances",
            headers=headers,
        )
        assert balances.json()[0]["current_balance"] == "19000.00"

        net_worth = await client.get(
            "/api/v1/finance/net-worth",
            headers=headers,
        )
        assert net_worth.status_code == 200, net_worth.text
        assert net_worth.json()["account_assets"] == "19000.00"
        assert net_worth.json()["net_worth"] == "19000.00"

        deleted = await client.delete(
            f"/api/v1/finance/transactions/{transaction_id}",
            headers=headers,
        )
        assert deleted.status_code == 204, deleted.text

        balances = await client.get(
            "/api/v1/finance/accounts/balances",
            headers=headers,
        )
        assert balances.json()[0]["current_balance"] == "15000.00"

        transactions = await client.get(
            "/api/v1/finance/transactions",
            headers=headers,
        )
        assert all(
            item["id"] != transaction_id
            for item in transactions.json()
        )

        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200, me.text
