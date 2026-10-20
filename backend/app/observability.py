"""
Structured Logging & Observability Configuration (Module 8)
===========================================================
Configures application-wide structured JSON logging with correlation IDs.

SE Concepts Applied:
  - Observability Pillar 1 (Logs): Structured JSON output with context fields.
  - Correlation IDs: Every request gets a UUID injected into all log records
    within that request's lifetime, enabling full trace across Router → Agent
    → LLM → Tool → DB → Response.
  - Log Levels: DEBUG for development, INFO for staging, WARNING+ for production.

Usage:
  from backend.app.observability import configure_logging, get_logger
  configure_logging()
  logger = get_logger("campuslife.voice.agent")
  logger.info("intent_dispatched", extra={"user_id": 1, "intent": "GET_TASKS"})

FastAPI Middleware:
  app.add_middleware(CorrelationIDMiddleware)
  — Automatically injects X-Correlation-ID header and log context per request.
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# ---------------------------------------------------------------------------
# Correlation ID context variable (thread/async safe)
# ---------------------------------------------------------------------------
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


# ---------------------------------------------------------------------------
# Structured JSON Log Formatter
# ---------------------------------------------------------------------------
class StructuredJSONFormatter(logging.Formatter):
    """
    Emits every log record as a single-line JSON object.
    Fields included: timestamp, level, logger, correlation_id, message, + extras.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": get_correlation_id() or "—",
            "msg": record.getMessage(),
        }
        # Include any extra fields passed via logger.info("...", extra={...})
        skip_keys = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "taskName",
        }
        for key, val in record.__dict__.items():
            if key not in skip_keys:
                log_obj[key] = val

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
def configure_logging(level: str = "INFO") -> None:
    """
    Configures the root logger with structured JSON output.
    Call once at application startup (in main.py).

    Args:
        level: Log level string ("DEBUG", "INFO", "WARNING", "ERROR").
    """
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("campuslife").info(
        "logging_configured",
        extra={"level": level, "format": "structured_json"},
    )


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper — returns a named logger under the campuslife namespace."""
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Correlation ID Middleware
# ---------------------------------------------------------------------------
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that:
    1. Reads X-Correlation-ID from the incoming request header (if present).
    2. Generates a new UUID if no ID was provided.
    3. Injects the ID into the async context variable so all log records
       within this request's lifecycle automatically include it.
    4. Echoes the correlation ID back in the response header.

    This enables full end-to-end tracing of a single voice query through:
    Router → VoiceAgent → LLMEngine → campuslife_tools → SQLAlchemy → Response
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Accept correlation ID from upstream (e.g., API gateway) or generate fresh
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(cid)

        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 1)

        # Attach to response so clients can trace their requests
        response.headers["X-Correlation-ID"] = cid
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        logging.getLogger("campuslife.http").info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
