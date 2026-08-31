"""The global error boundary.

An unhandled exception must produce three things: a 500 the client can parse, a log line
with the full traceback, and a request ID the citizen can quote. What it must **not**
produce is a stack trace in the response body — a traceback names internal paths, table
names and library versions, and a government service should not hand those to anyone who
can send a malformed request.

The validation handler exists for a different reason. FastAPI's default 422 body is a
list of `loc`/`msg`/`type` objects that assumes the reader knows Pydantic. This turns it
into one sentence naming the field, because the thing consuming this API is sometimes a
partner's integration team debugging at 6pm.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import current_request_id
from app.core.middleware import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


def _body(detail: str, extra: dict | None = None) -> dict:
    return {"detail": detail, "request_id": current_request_id(), **(extra or {})}


def _headers() -> dict[str, str]:
    return {REQUEST_ID_HEADER: current_request_id()}


def install(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Expected, deliberate responses — 404, 403, 409. Logged at info, not error:
        # a partner trying an illegal transition is the system working.
        logger.info(
            "http_error",
            extra={"path": request.url.path, "status": exc.status_code, "detail": str(exc.detail)},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(str(exc.detail)),
            headers={**_headers(), **(exc.headers or {})},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        problems = []
        for error in exc.errors():
            # Drop the leading "body"/"query" segment; the field name is what matters.
            location = ".".join(str(part) for part in error.get("loc", ()) if part != "body")
            problems.append(f"{location or 'request'}: {error.get('msg', 'is invalid')}")

        logger.info(
            "validation_error",
            extra={"path": request.url.path, "problems": problems[:5]},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_body(
                "; ".join(problems[:5]) or "The request could not be understood.",
                {"problems": problems},
            ),
            headers=_headers(),
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Full detail to the log, none of it to the client.
        logger.exception(
            "unhandled_exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
            },
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_body(
                "Something went wrong at our end. Please try again. "
                "If it keeps happening, quote this reference to support."
            ),
            headers=_headers(),
        )
