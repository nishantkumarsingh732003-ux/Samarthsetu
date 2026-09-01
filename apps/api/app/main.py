import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core import errors
from app.core import logging as log_setup
from app.core.config import settings
from app.core.middleware import (
    RateLimitMiddleware,
    RejectNullBytes,
    RequestContextMiddleware,
)

log_setup.configure()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm caches and load the versioned rule pack.
    from setu_rules import ENGINE_VERSION, rules_digest

    logger.info(
        "startup",
        extra={
            "engine_version": ENGINE_VERSION,
            "rules_digest": rules_digest(),
            "llm_provider": settings.LLM_PROVIDER,
            "notification_driver": settings.NOTIFICATION_DRIVER,
            "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        },
    )
    yield
    # Shutdown: close pools.
    from app.core import cache

    await cache.close()


app = FastAPI(
    title="SETU API",
    description="Scheme Eligibility & Transparent Uptake — SIH 2026 PS 26092 (MoSJE)",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware runs bottom-up on the way in, so the request ID is assigned *before* the
# rate limiter can reject anything — a 429 still carries an ID the citizen can quote.
app.add_middleware(RejectNullBytes)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    # Development only; None in production. See `Settings.allowed_origin_regex`.
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
)

errors.install(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["meta"])
async def readyz() -> dict[str, object]:
    """Liveness is not readiness.

    `/health` says the process is up. This says what it can currently reach, so an
    operator can tell "the model provider is down but eligibility still works" — which
    is the exact degradation this service is designed to survive — from "the database is
    gone and nothing works". Neither answer changes the status code: a service that
    still decides eligibility correctly with the LLM offline is healthy, and taking it
    out of rotation for that would be the bug.
    """
    from sqlalchemy import text

    from app.core import cache
    from app.db.session import SessionLocal
    from app.services import llm

    checks: dict[str, object] = {}

    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 - the point is to report, not to raise
        checks["database"] = f"unavailable: {type(exc).__name__}"

    try:
        await cache.get_client().ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"unavailable: {type(exc).__name__}"

    provider = llm.resolve_provider()
    # Configuration, not reachability. Probing the provider here would put a paid,
    # multi-second network call on a path an orchestrator hits every few seconds — and
    # it would not change the answer, because eligibility does not depend on it. The
    # field is named for what it actually reports so nobody reads "llm: groq" during an
    # outage and concludes the model is answering.
    checks["llm_provider_configured"] = str(provider)
    checks["llm_required_for_eligibility"] = False
    checks["eligibility_available"] = checks["database"] == "ok"

    return {"status": "ok", "checks": checks}
