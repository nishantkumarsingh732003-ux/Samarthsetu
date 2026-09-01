.PHONY: up down seed demo api web test lint fmt migrate rules chaos bench

up:      ; docker compose up -d
down:    ; docker compose down
seed:    ; docker compose exec api python /scripts/seed/run.py
# The whole demo world in one command: reference data, then the three personas and
# a background population built by running the real services.
demo:    ; docker compose exec api python /scripts/seed/run.py && docker compose exec api python /scripts/seed/demo.py
api:     ; cd apps/api && uvicorn app.main:app --reload --port 8000
web:     ; pnpm --filter @setu/web dev
migrate: ; cd apps/api && alembic upgrade head
test:    ; python -m pytest packages/rules -q && cd apps/api && pytest -q && cd ../.. && pnpm -r test
lint:    ; cd apps/api && ruff check . && mypy app && cd ../.. && pnpm -r lint
fmt:     ; cd apps/api && ruff format . && cd ../.. && pnpm -r format

# Recompile the rule bundle + golden snapshot after editing packages/rules/schemes/*.yaml
rules:   ; python packages/rules/scripts/regenerate_golden.py
# Kill the language model and prove a full citizen journey still completes.
chaos:   ; bash scripts/chaos.sh
# Measure eligibility latency. The limiter has to be off, or we measure the limiter.
bench:   ; RATE_LIMIT_ENABLED=false docker compose up -d --force-recreate api && sleep 6 && docker compose exec api python /scripts/bench.py; docker compose up -d --force-recreate api
