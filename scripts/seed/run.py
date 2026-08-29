"""Seed runner.

Usage:
    python scripts/seed/run.py            # run every registered seeder
    python scripts/seed/run.py schemes    # run named seeders only
    python scripts/seed/run.py --list     # show what is registered

Seeders are registered in `SEEDERS` below, in dependency order. Each one must be
idempotent: running the seeder twice leaves the database in the same state as running
it once, so `make seed` is safe to repeat during a demo.

CLAUDE.md rule 6 — no mock data in the demo path. Seeders write real rows to the real
database; screens are never populated from fixtures held in the frontend.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

# The API package sits at <repo>/apps/api on a developer machine and at /app inside the
# container, where this file is mounted at /scripts. Try both rather than assuming one.
REPO_ROOT = Path(__file__).resolve().parents[2]
# `scripts` is imported as a package (scripts.seed.partners), so its parent must be on
# the path. In the container scripts/ is mounted at /scripts, so that parent is /.
for parent in (REPO_ROOT, Path("/")):
    if (parent / "scripts" / "seed" / "run.py").is_file():
        sys.path.insert(0, str(parent))
        break

for candidate in (REPO_ROOT / "apps" / "api", Path("/app")):
    if (candidate / "app" / "db" / "session.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:  # pragma: no cover - only reachable from an unexpected layout
    raise SystemExit(
        "Cannot locate the API package (looked for app/db/session.py under "
        f"{REPO_ROOT / 'apps' / 'api'} and /app)."
    )

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.session import SessionLocal, engine  # noqa: E402

from scripts.seed.partners import seed_partners  # noqa: E402
from scripts.seed.schemes import seed_schemes  # noqa: E402

Seeder = Callable[[AsyncSession], Awaitable[str]]

REQUIRED_EXTENSIONS = ("postgis", "vector")

# Order matters: partner authorisations reference scheme rows.
# Phase 8 appends the demo personas and applications.
SEEDERS: dict[str, Seeder] = {
    "schemes": seed_schemes,
    "partners": seed_partners,
}


async def verify_extensions(session: AsyncSession) -> None:
    """Fail loudly if the database was not initialised with PostGIS and pgvector."""
    result = await session.execute(text("SELECT extname FROM pg_extension"))
    installed = {row[0] for row in result}
    missing = [e for e in REQUIRED_EXTENSIONS if e not in installed]
    if missing:
        raise SystemExit(
            f"Missing PostgreSQL extension(s): {', '.join(missing)}.\n"
            "These are installed by scripts/seed/00_extensions.sql on first container "
            "start. If the volume predates that file, run "
            "`docker compose down -v && docker compose up`."
        )


async def run(selected: list[str] | None = None) -> int:
    names = selected or list(SEEDERS)
    unknown = [n for n in names if n not in SEEDERS]
    if unknown:
        raise SystemExit(f"Unknown seeder(s): {', '.join(unknown)}. Known: {', '.join(SEEDERS) or 'none'}")

    async with SessionLocal() as session:
        await verify_extensions(session)

        if not names:
            print("No seeders registered yet — extensions verified, nothing to load.")
            return 0

        for name in names:
            summary = await SEEDERS[name](session)
            await session.commit()
            print(f"  {name}: {summary}")

    return len(names)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load SETU reference and demo data.")
    parser.add_argument("seeders", nargs="*", help="Seeder names to run (default: all).")
    parser.add_argument("--list", action="store_true", help="List registered seeders and exit.")
    args = parser.parse_args()

    if args.list:
        print("\n".join(SEEDERS) or "(none registered yet)")
        return

    async def _main() -> None:
        try:
            count = await run(args.seeders or None)
        finally:
            await engine.dispose()
        print(f"Done. {count} seeder(s) ran.")

    asyncio.run(_main())


if __name__ == "__main__":
    main()
