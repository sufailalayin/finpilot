# FinPilot Hosting Setup

FinPilot is designed to run as separate production services.

## Service 1: PostgreSQL

Create a managed PostgreSQL database and place its async connection string in:

`FINPILOT_DATABASE_URL`

Example format:

`postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE`

## Service 2: Backend API

Deploy from the repository's `backend/` directory.

Use `backend/railway.json` or the backend Dockerfile.

Required minimum variables:

- `FINPILOT_ENVIRONMENT=production`
- `FINPILOT_DATABASE_URL`
- `FINPILOT_REDIS_URL`
- `FINPILOT_JWT_SECRET`
- `FINPILOT_CORS_ORIGINS`

Optional until enabled:

- `FINPILOT_OPENAI_API_KEY`
- `FINPILOT_OPENAI_MODEL`
- `FINPILOT_GOOGLE_PLAY_PACKAGE_NAME`
- `FINPILOT_GOOGLE_PLAY_MONTHLY_PRODUCT_ID`
- `FINPILOT_GOOGLE_PLAY_YEARLY_PRODUCT_ID`
- `FINPILOT_GOOGLE_PLAY_SERVICE_ACCOUNT_JSON`
- `FINPILOT_GOOGLE_PLAY_RTDN_SECRET`

Backend readiness:

`/api/v1/ready`

## Service 3: Admin Web

Deploy from the repository's `admin/` directory.

Set:

`NEXT_PUBLIC_FINPILOT_API_BASE_URL=https://YOUR-BACKEND-DOMAIN/api/v1`

Then add the admin site's origin to backend:

`FINPILOT_CORS_ORIGINS=https://YOUR-ADMIN-DOMAIN`

## First admin

After backend deployment:

```bash
python -m app.cli.create_admin   --email YOUR_ADMIN_EMAIL   --password 'YOUR_STRONG_PASSWORD'   --name 'Hastron Ventures Admin'
```

## Android production API

Build Android with:

```bash
flutter build appbundle --release   --dart-define=FINPILOT_API_BASE_URL=https://YOUR-BACKEND-DOMAIN/api/v1
```

The Android app must never contain database, OpenAI, Google service-account, or admin secrets.
