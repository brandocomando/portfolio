"""Structured Telemetry, Request Tracing, and Logging.

Injects W3C traceparent or generates deterministic request trace IDs for distributed tracing.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] [trace_id=%(trace_id)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)

logger = logging.getLogger("portfolio.api")


class TraceContextFilter(logging.Filter):
    trace_id: str = "no-trace"

    def filter(self, record):
        record.trace_id = getattr(TraceContextFilter, "trace_id", "no-trace")
        return True


logger.addFilter(TraceContextFilter())
logging.getLogger().addFilter(TraceContextFilter())
for handler in logging.root.handlers:
    handler.addFilter(TraceContextFilter())


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("x-trace-id") or request.headers.get("traceparent")
        if not trace_id:
            trace_id = f"trace-{uuid.uuid4().hex[:12]}"

        TraceContextFilter.trace_id = trace_id
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)"
        )
        return response
