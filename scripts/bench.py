"""Measure eligibility latency, and say where the time actually goes.

    RATE_LIMIT_ENABLED=false docker compose up -d --force-recreate api
    docker compose exec api python /scripts/bench.py
    docker compose up -d --force-recreate api        # restore the limiter

The non-functional requirement is "eligibility p95 under 500 ms". It sat in
PRODUCT_REQUIREMENTS.md marked *not measured*, which is a claim rather than a fact.

Three layers are measured separately, because one end-to-end number would hide the thing
worth knowing:

  1. **The rule engine alone** — a pure function, no I/O. The floor, and what a citizen's
     device would pay if the TypeScript engine ever evaluates offline.
  2. **`/match` over HTTP** — adds FastAPI, Pydantic, the `match_runs` write and an audit
     row. The gap between this and (1) is the cost of *recording* the decision, which is
     a governance requirement rather than overhead to be optimised away.
  3. **`/partners/route`** — adds PostGIS distance over 60 candidates. The heaviest read
     in the product, and the one a reviewer asks about.

Percentiles, never a mean: one 400 ms outlier moves a mean enough to hide that everything
else answered in 12 ms, and p95 is what the requirement is written against.

The rate limiter has to be off for this. 300 requests a minute trips our own 120/min
budget, and measuring the limiter is not measuring the service.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve()
for candidate in (_HERE.parents[1], Path("/app"), _HERE.parents[1] / "apps" / "api"):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import httpx  # noqa: E402

BASE = "http://localhost:8000"
TARGET_P95_MS = 500.0

# The persona the demo script opens with, so the number quoted on stage is this number.
SUNITA: dict[str, Any] = {
    "category": "SC",
    "project_sector": "TRADE",
    "occupation_type": "Vegetable vendor",
    "annual_family_income": 180000,
    "project_cost": 80000,
}


class RateLimited(RuntimeError):
    """Our own middleware refused the run. Not what is being measured."""


def explain_rate_limit() -> None:
    print()
    print("  Rate limited by our own middleware, which is doing its job.")
    print("  Re-run with the limiter off; it is not what is being measured:")
    print()
    print("    RATE_LIMIT_ENABLED=false docker compose up -d --force-recreate api")
    print("    docker compose exec api python /scripts/bench.py")
    print("    docker compose up -d --force-recreate api        # restore")
    print()


def percentiles(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)

    def at(q: float) -> float:
        # Nearest-rank: for 300 samples p95 is the 285th, an actual observation rather
        # than an interpolation between two of them.
        index = min(len(ordered) - 1, max(0, round(q * len(ordered)) - 1))
        return ordered[index]

    return {
        "min": ordered[0],
        "p50": at(0.50),
        "p95": at(0.95),
        "p99": at(0.99),
        "max": ordered[-1],
        "mean": statistics.fmean(ordered),
    }


def measure(label: str, call: Callable[[], Any], n: int, warmup: int = 20) -> dict[str, float]:
    """Time `call` n times after discarding a warm-up.

    The warm-up is not cheating: the first calls pay for import caching and a connection
    pool that has not opened yet. A citizen's tenth request is a fairer picture of the
    service than their first — and the first is reported anyway, as `cold`, so nothing is
    hidden.
    """
    cold = 0.0
    for i in range(warmup):
        started = time.perf_counter()
        call()
        if i == 0:
            cold = (time.perf_counter() - started) * 1000

    samples: list[float] = []
    for _ in range(n):
        started = time.perf_counter()
        try:
            call()
        except httpx.HTTPStatusError as exc:
            # The up-front probe only sees the first request; the limiter bites part way
            # through a run, so it has to be caught here too.
            if exc.response.status_code == 429:
                raise RateLimited from None
            raise
        samples.append((time.perf_counter() - started) * 1000)

    stats = percentiles(samples)
    stats["cold"] = cold

    verdict = ""
    if "match" in label:
        verdict = "   PASS" if stats["p95"] < TARGET_P95_MS else "   FAIL"

    print(
        f"  {label:<32} "
        f"p50 {stats['p50']:7.2f}  p95 {stats['p95']:7.2f}  p99 {stats['p99']:7.2f}  "
        f"max {stats['max']:7.2f}  (cold {stats['cold']:.1f}){verdict}"
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure SamarthSetu eligibility latency.")
    parser.add_argument("--n", type=int, default=300, help="samples per stage")
    args = parser.parse_args()

    print("SamarthSetu latency — milliseconds, percentiles not means")
    print()

    from setu_rules import ENGINE_VERSION, run

    print(f"1. Rule engine, in process (engine {ENGINE_VERSION}, no I/O)")
    engine = measure("evaluate + rank + fit", lambda: run(SUNITA, language="en"), args.n)

    try:
        httpx.get(f"{BASE}/health", timeout=2.0).raise_for_status()
    except Exception:  # noqa: BLE001 - any failure means "not running"
        print()
        print("  API not reachable — skipping the HTTP stages.")
        print("  Start it with: docker compose up -d")
        raise SystemExit(0) from None

    client = httpx.Client(base_url=BASE, timeout=30.0)

    def match() -> None:
        client.post(
            "/api/v1/match", json={"profile": SUNITA, "language": "en"}
        ).raise_for_status()

    def route() -> None:
        client.post(
            "/api/v1/partners/route",
            json={"scheme_code": "NSFDC_MICRO_FINANCE", "amount": 72000, "district": "Nagpur"},
        ).raise_for_status()

    http: dict[str, float] = {}
    try:
        # Fail fast rather than mid-run inside a traceback.
        probe = client.post("/api/v1/match", json={"profile": SUNITA, "language": "en"})
        if probe.status_code == 429:
            raise RateLimited

        print()
        print("2. Over HTTP (adds FastAPI, Pydantic, the match_runs write and an audit row)")
        http = measure("POST /api/v1/match", match, args.n)

        print()
        print("3. The heaviest read (PostGIS distance over 60 candidates)")
        measure("POST /api/v1/partners/route", route, args.n)
    except RateLimited:
        explain_rate_limit()
        raise SystemExit(0) from None
    finally:
        client.close()

    recording = http["p50"] - engine["p50"]
    print()
    print("Where the time goes, at p50:")
    print(f"  deciding   {engine['p50']:7.2f} ms   the rule engine itself")
    print(f"  recording  {recording:7.2f} ms   HTTP, validation, match_runs, audit")
    print()
    print("  The second number buys a decision that is replayable months later.")
    print("  It is a governance requirement, not overhead to be optimised away.")

    passed = http["p95"] < TARGET_P95_MS
    print()
    print(
        f"Requirement: eligibility p95 < {TARGET_P95_MS:.0f} ms  ->  "
        f"{http['p95']:.2f} ms  {'PASS' if passed else 'FAIL'}"
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
