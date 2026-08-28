#!/usr/bin/env bash
# Applies migrations before serving, so `docker compose up` from a clean clone yields
# a working API against a fully-migrated database with no manual step.
set -euo pipefail

echo "==> Waiting for Postgres"
until python -c "
import asyncio, os, sys, asyncpg
url = os.environ['DATABASE_URL'].replace('+asyncpg', '')
async def main():
    conn = await asyncpg.connect(url)
    await conn.close()
asyncio.run(main())
" 2>/dev/null; do
  sleep 1
done

echo "==> alembic upgrade head"
alembic upgrade head

echo "==> Starting API on :8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
