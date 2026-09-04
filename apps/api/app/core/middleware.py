"""Request-scoped middleware: tracing, timing, and rate limiting.

Three things, in the order they must run.

`RequestContextMiddleware` assigns or adopts a request ID and puts it on every log line
and every response header. A citizen reporting "it broke" can read the ID off the error
screen, and one `grep` finds the whole request.

`RateLimitMiddleware` is a fixed-window counter in Redis. Deliberately generous, and
deliberately **fail-open**: if Redis is unreachable the request is served rather than
refused. Rate limiting exists to stop a runaway script, and a cache outage must not
become an outage of the eligibility service — that trade is the wrong way round for a
government service people are relying on.

Both are pure ASGI-adjacent middleware rather than dependencies, because they must also
cover requests that never reach a route: 404s, malformed bodies, and the errors the
global handler turns into responses.
"""

from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core import cache
from app.core.config import settings
from app.core.logging import current_request_id, new_request_id, request_id_var

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

# Paths that must never be rate limited or noisily logged: an orchestrator polling
# health at 1Hz would otherwise exhaust the window and take the service out of rotation
# for the exact reason it was checking.
EXEMPT_PATHS = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Adopt an upstream ID when there is one, so a trace survives a proxy hop.
        incoming = request.headers.get(REQUEST_ID_HEADER, "").strip()
        request_id = incoming[:64] if incoming else new_request_id()
        token = request_id_var.set(request_id)
        request.state.request_id = request_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            request_id_var.reset(token)

        response.headers[REQUEST_ID_HEADER] = request_id
        if request.url.path not in EXEMPT_PATHS:
            logger.info(
                "request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": elapsed_ms,
                    # The client address, never the query string: a routing call carries
                    # a citizen's coordinates and those do not belong in an access log.
                    "client": request.client.host if request.client else None,
                },
            )
        return response


class RejectNullBytes(BaseHTTPMiddleware):
    """Refuse input PostgreSQL physically cannot store, before it reaches PostgreSQL.

    A NUL byte is legal in JSON (as \u0000) and legal in a percent-encoded URL (`%00`),
    but Postgres `text` and `jsonb` cannot hold one. So it travels happily through
    Pydantic, through the rule engine, and dies inside asyncpg as an unhandled error —
    a 500 on a public, unauthenticated endpoint, which is an information disclosure
    whether or not the payload achieved anything.

    Found by `tests/test_security_surface.py`, which is what that file is for.

    Rejected at the edge rather than sanitised: a NUL in a citizen's occupation or a
    reference number is never a legitimate value, and silently stripping it would store
    something the citizen did not type.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # `request.url.path` is already percent-decoded, so this catches %00 too.
        if "\x00" in request.url.path:
            return self._refuse("the web address")

        # The third door, and the one this guard originally missed: a query parameter.
        # `GET /partners/directory?q=%00x` reached an ILIKE and died inside asyncpg as a
        # 500 on a public endpoint — the same bug as the path case, through a door nobody
        # had shut. `query_params` is decoded, so this catches the percent-encoded form.
        for value in request.query_params.values():
            if "\x00" in value:
                return self._refuse("the search you sent")

        if request.method in {"POST", "PUT", "PATCH"}:
            # Caching the body here is safe: Starlette memoises it, so the route's own
            # `await request.json()` reuses these bytes rather than re-reading a
            # consumed stream.
            body = await request.body()
            if b"\x00" in body or rb"\u0000" in body:
                return self._refuse("the information you sent")

        return await call_next(request)

    @staticmethod
    def _refuse(what: str) -> JSONResponse:
        logger.warning("null_byte_rejected")
        return JSONResponse(
            status_code=400,
            content={
                "detail": (
                    f"There is an invalid character in {what}. "
                    "Please retype it and try again."
                ),
                "request_id": current_request_id(),
            },
            headers={REQUEST_ID_HEADER: current_request_id()},
        )


def _limit_for(path: str) -> tuple[str, int]:
    """Which bucket this path counts against, and how many it allows.

    Grouped rather than per-path: a citizen who taps through six screens should not be
    metered as six separate allowances, and a script hammering one endpoint should not
    get a fresh budget by varying the URL.
    """
    if path.endswith("/conversation/turn") or path.endswith("/webhook/whatsapp"):
        # Costs a model call and a Redis session write.
        return "conversation", settings.RATE_LIMIT_CONVERSATION
    if path.endswith("/auth/login"):
        # Metered hardest: this is the only endpoint worth brute-forcing.
        return "login", settings.RATE_LIMIT_LOGIN
    return "default", settings.RATE_LIMIT_DEFAULT


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if not settings.RATE_LIMIT_ENABLED or path in EXEMPT_PATHS:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        group, limit = _limit_for(path)
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        bucket = int(time.time() // window)
        key = f"setu:rl:{group}:{bucket}:{client}"

        try:
            redis = cache.get_client()
            count = await redis.incr(key)
            if count == 1:
                # Only the first writer sets the TTL, so the window does not slide
                # forward on every hit and trap a client indefinitely.
                await redis.expire(key, window)
        except Exception as exc:  # noqa: BLE001 - fail open, see the module docstring
            logger.warning("rate limit unavailable, serving anyway: %s", exc)
            return await call_next(request)

        if count > limit:
            retry_after = window - int(time.time() % window)
            logger.warning(
                "rate_limited",
                extra={"path": path, "client": client, "count": count, "limit": limit},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many requests from this connection. "
                        f"Please wait {retry_after} seconds and try again."
                    ),
                    "request_id": current_request_id(),
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    REQUEST_ID_HEADER: current_request_id(),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
