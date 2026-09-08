import argparse
import datetime as dt
import sys

import httpx


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    client = httpx.Client(base_url=base, timeout=20.0)

    ready = client.get("/ready")
    ready.raise_for_status()
    require(ready.json().get("status") == "ready", "Backend is not ready")

    login = client.post(
        "/auth/login",
        json={"email": args.email, "password": args.password},
    )

    if login.status_code == 401:
        register = client.post(
            "/auth/register",
            json={
                "email": args.email,
                "password": args.password,
                "full_name": "FinPilot Smoke Test",
            },
        )
        register.raise_for_status()
        token = register.json()["access_token"]
    else:
        login.raise_for_status()
        token = login.json()["access_token"]

    headers = {"Authorization": "Bearer " + token}

    me = client.get("/auth/me", headers=headers)
    me.raise_for_status()
    require(me.json()["email"].lower() == args.email.lower(), "Authenticated user mismatch")

    status = client.get("/subscriptions/status", headers=headers)
    status.raise_for_status()
    require(status.json()["status"] in {"trial", "active", "expired", "cancelled"}, "Unknown subscription status")

    accounts_response = client.get("/finance/accounts", headers=headers)
    accounts_response.raise_for_status()
    accounts = accounts_response.json()

    if accounts:
        account_id = accounts[0]["id"]
    else:
        created = client.post(
            "/finance/accounts",
            headers=headers,
            json={
                "name": "Smoke Test Cash",
                "account_type": "cash",
                "currency": "INR",
                "opening_balance": 1000,
            },
        )
        created.raise_for_status()
        account_id = created.json()["id"]

    today = dt.date.today().isoformat()
    tx = client.post(
        "/finance/transactions",
        headers=headers,
        json={
            "account_id": account_id,
            "category_id": None,
            "transaction_type": "expense",
            "amount": 1,
            "occurred_on": today,
            "merchant": "FinPilot Smoke Test",
            "note": "Automated deployment smoke test",
        },
    )
    tx.raise_for_status()

    dashboard = client.get("/dashboard", headers=headers)
    dashboard.raise_for_status()
    require("summary" in dashboard.json(), "Dashboard summary missing")

    budgets = client.get("/planning/budgets", headers=headers)
    budgets.raise_for_status()

    goals = client.get("/planning/goals", headers=headers)
    goals.raise_for_status()

    ai = client.post(
        "/ai/ask",
        headers=headers,
        json={"question": "Give me a short summary of my finances."},
    )
    if status.json()["status"] in {"trial", "active"}:
        ai.raise_for_status()
        require(bool(ai.json().get("answer")), "AI response missing")

    print("FINPILOT LIVE SMOKE: PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FINPILOT LIVE SMOKE: FAILED:", exc, file=sys.stderr)
        raise
