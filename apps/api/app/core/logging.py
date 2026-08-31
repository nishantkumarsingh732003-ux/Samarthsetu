"""Structured logging, and the request ID that ties a citizen's complaint to a trace.

Every log line is one JSON object on one line. Prose logs are pleasant to read on a
laptop and useless in a container, where the only tools are `grep` and `jq` — and the
question being asked at 2am is always "what happened to request X", which needs a field,
not a sentence.

`request_id` is carried in a `ContextVar` rather than passed through call signatures, so
a log line written five layers down in the rule engine still reports which request it
belonged to without every function in between growing a parameter it does not use.

The formatter is deliberately defensive about one thing: a log record whose `extra`
contains something unserialisable must still produce a line. Losing the message you were
trying to log because the logger itself raised is the worst possible failure mode for
logging.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from app.core.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# Attributes LogRecord always carries. Anything else came from `extra=` and is ours.
_RESERVED = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"asctime", "message", "taskName"}


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def current_request_id() -> str:
    return request_id_var.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or request_id_var.get(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        try:
            return json.dumps(payload, ensure_ascii=False, default=str)
        except Exception:  # noqa: BLE001 - a logger that raises loses the message entirely
            return json.dumps(
                {
                    "ts": payload["ts"],
                    "level": record.levelname,
                    "logger": record.name,
                    "msg": record.getMessage(),
                    "request_id": payload["request_id"],
                    "log_format_error": "extra fields were not serialisable",
                },
                ensure_ascii=False,
            )


class RequestIdFilter(logging.Filter):
    """Stamps every record, including ones from libraries that know nothing about us."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        return True


def configure() -> None:
    """Install the formatter on the root logger and align uvicorn's loggers with it."""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        JsonFormatter()
        if settings.LOG_JSON
        else logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
    )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL.upper())

    # uvicorn installs its own handlers; without this its error log stays plain text
    # while everything else is JSON, which is the worst of both.
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False

    # uvicorn's access log is silenced rather than reformatted. It writes one line per
    # request that duplicates `RequestContextMiddleware`, and it runs outside the
    # ContextVar scope, so its copy always carries an empty request_id — two lines per
    # request, one of them untraceable.
    access = logging.getLogger("uvicorn.access")
    access.handlers = []
    access.propagate = False
    access.disabled = True

    # SQLAlchemy's echo is per-statement and swamps everything at DEBUG.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
