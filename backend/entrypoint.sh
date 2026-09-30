#!/usr/bin/env sh
set -eu

alembic upgrade head

if [ -n "${FINPILOT_BOOTSTRAP_ADMIN_EMAIL:-}" ] && [ -n "${FINPILOT_BOOTSTRAP_ADMIN_PASSWORD:-}" ]; then
  python -m app.cli.create_admin \
    --email "$FINPILOT_BOOTSTRAP_ADMIN_EMAIL" \
    --password "$FINPILOT_BOOTSTRAP_ADMIN_PASSWORD" \
    --name "${FINPILOT_BOOTSTRAP_ADMIN_NAME:-}"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
