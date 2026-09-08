# FinPilot Deployment

Run backend migrations before starting the API:

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Important production values:
- FINPILOT_DATABASE_URL
- FINPILOT_REDIS_URL
- FINPILOT_JWT_SECRET
- FINPILOT_OPENAI_API_KEY
- FINPILOT_OPENAI_MODEL
- FINPILOT_GOOGLE_PLAY_PACKAGE_NAME

If FINPILOT_OPENAI_API_KEY is empty, FinPilot uses its local fallback analysis.

For Android:
```bash
flutter build appbundle --dart-define=FINPILOT_API_BASE_URL=https://api.example.com/api/v1
```

Never place server secrets in the Flutter application.
