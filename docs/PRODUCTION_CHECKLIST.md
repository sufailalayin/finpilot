# FinPilot Production Checklist

## Backend

Required production environment variables:

- FINPILOT_ENVIRONMENT=production
- FINPILOT_DATABASE_URL
- FINPILOT_REDIS_URL
- FINPILOT_JWT_SECRET
- FINPILOT_CORS_ORIGINS
- FINPILOT_OPENAI_API_KEY
- FINPILOT_OPENAI_MODEL
- FINPILOT_GOOGLE_PLAY_PACKAGE_NAME
- FINPILOT_GOOGLE_PLAY_MONTHLY_PRODUCT_ID
- FINPILOT_GOOGLE_PLAY_YEARLY_PRODUCT_ID
- FINPILOT_GOOGLE_PLAY_SERVICE_ACCOUNT_JSON
- FINPILOT_GOOGLE_PLAY_RTDN_SECRET

Run migrations before serving traffic.

Health endpoints:

- `/api/v1/health`
- `/api/v1/ready`

## Create the first admin

From the backend environment:

```bash
python -m app.cli.create_admin   --email admin@example.com   --password 'replace-with-a-strong-password'   --name 'FinPilot Admin'
```

Use a unique admin email and strong password. Do not commit them.

## Admin site

Set:

- NEXT_PUBLIC_FINPILOT_API_BASE_URL=https://api.example.com/api/v1

Ensure the admin site's origin is included in FINPILOT_CORS_ORIGINS.

## Android

Use the production API URL when building:

```bash
flutter build appbundle --release   --dart-define=FINPILOT_API_BASE_URL=https://api.example.com/api/v1
```

## End-to-end smoke test

1. Register a new Android user.
2. Confirm 7-day Pro trial.
3. Create an account.
4. Add income and expense.
5. Verify dashboard totals.
6. Create a budget and savings goal.
7. Ask FinPilot AI a question.
8. Open FinPilot Pro paywall.
9. Test Google Play purchase on internal testing track.
10. Confirm backend entitlement activation.
11. Confirm admin dashboard user/trial/AI metrics.
12. Confirm RTDN renewal/cancellation updates.
