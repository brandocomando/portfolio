"""Main FastAPI Application Entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.telemetry import RequestTracingMiddleware
from backend.app.core.client_auth import ClientVerificationMiddleware
from backend.app.api.router import api_v1_router
from backend.app.api.v1.health import router as root_health_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend AI & RAG retrieval service for Brandon Foster's portfolio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Client Verification Middleware (checks custom verification header on /api routes)
app.add_middleware(ClientVerificationMiddleware)

# 2. CORS Middleware (evaluates origin against settings.CORS_ORIGINS and attaches CORS headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Tracing Middleware (outermost: logs request lifecycle and attaches X-Trace-ID)
app.add_middleware(RequestTracingMiddleware)

# Include Routers
app.include_router(root_health_router)  # Top level /healthz, /readyz, /metrics
app.include_router(api_v1_router)       # /api/v1/chat, /api/v1/leads, /api/v1/health


@app.get("/", summary="Root Index")
async def root():
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "health": "/healthz",
        "api_v1": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
