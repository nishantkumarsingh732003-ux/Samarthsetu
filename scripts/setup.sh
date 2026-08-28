#!/usr/bin/env bash
set -euo pipefail

echo "==> API deps"
python -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
pip install -r apps/api/requirements-dev.txt

echo "==> Web deps"
corepack enable
pnpm install

echo "Done. Run 'make up' for the full stack, or 'make api' and 'make web' separately."
