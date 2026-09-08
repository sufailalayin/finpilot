# Live Smoke Testing

After deploying the backend, run the GitHub Actions workflow **FinPilot Live Smoke**.

Required GitHub secrets:

- `FINPILOT_SMOKE_EMAIL`
- `FINPILOT_SMOKE_PASSWORD`

The workflow asks for the deployed API base URL, including `/api/v1`.

Example:

`https://api.example.com/api/v1`

It validates:

1. Database readiness
2. Login or registration
3. Current user
4. Trial/subscription status
5. Finance account creation/read
6. Expense transaction creation
7. Dashboard calculation
8. Budgets endpoint
9. Goals endpoint
10. AI response when Pro/trial access is active

Use a dedicated test account, not a real customer account. The smoke workflow intentionally leaves its test data in that dedicated account so it never needs a dangerous production-delete endpoint.
