"""Client Verification Middleware.

Ensures sensitive API endpoints can only be accessed by the verified portfolio web application,
while seamlessly permitting local development, Swagger docs, health checks, and CORS preflights.
"""

from typing import Callable
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.config import settings

logger = logging.getLogger("portfolio.security")

# Public system endpoints that bypass client verification
PUBLIC_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/healthz",
    "/readyz",
    "/metrics",
    "/api/v1/healthz",
    "/api/v1/readyz",
    "/api/v1/metrics",
}


class ClientVerificationMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing custom verification header on incoming API requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. CORS Preflights (OPTIONS) MUST pass through without validation
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # 2. Public and system endpoints bypass verification
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # 3. Only protect /api/ routes
        if not path.startswith("/api/"):
            return await call_next(request)

        # 4. If verification is disabled or running in test suite, permit
        if not settings.CLIENT_VERIFICATION_ENABLED or settings.ENV == "test":
            return await call_next(request)

        # 5. Check verification header
        header_name = settings.CLIENT_VERIFICATION_HEADER.lower()
        provided_secret = request.headers.get(header_name)

        if provided_secret == settings.CLIENT_VERIFICATION_SECRET:
            return await call_next(request)

        # 6. Local development convenience fallback:
        # In development or debug mode, allow requests from localhost / 127.0.0.1
        if settings.ENV == "development" or settings.DEBUG:
            client_host = request.client.host if request.client else ""
            origin = request.headers.get("origin", "")
            referer = request.headers.get("referer", "")
            host = request.headers.get("host", "")
            local_identifiers = ("localhost", "127.0.0.1", "testserver")
            if any(any(local in s for local in local_identifiers) for s in (client_host, origin, referer, host)):
                return await call_next(request)

        logger.warning(
            f"Blocked unauthorized API access to {path} from host={request.headers.get('host')}, "
            f"origin={request.headers.get('origin')}"
        )

        return JSONResponse(
            status_code=403,
            content={
                "detail": "Direct API access forbidden: missing or invalid client verification header"
            }
        )
