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

# PostGIS backs channel_partners.geom and pgvector backs semantic scheme search, so the
# first migration cannot run without both. Compose gets them from
# `docker-entrypoint-initdb.d` on a fresh volume; a managed database (Render, Railway,
# RDS) starts empty and never runs that, so the deploy died on the first geometry column
# with no hint as to why.
#
# `IF NOT EXISTS` makes this a no-op where they already exist. If the database user is
# not permitted to create extensions this warns and carries on rather than aborting: the
# migration is the honest place for that failure, and it names the missing extension.
echo "==> Ensuring postgis and vector extensions"
python - <<'PY' || echo "    ! could not create extensions — see docs/DEPLOYMENT.md"
import asyncio, os, asyncpg

url = os.environ["DATABASE_URL"].replace("+asyncpg", "")

async def main() -> None:
    conn = await asyncpg.connect(url)
    try:
        for extension in ("postgis", "vector"):
            await conn.execute(f"CREATE EXTENSION IF NOT EXISTS {extension}")
            print(f"    {extension} ready")
    finally:
        await conn.close()

asyncio.run(main())
PY

echo "==> alembic upgrade head"
alembic upgrade head

echo "==> Starting API on :8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
