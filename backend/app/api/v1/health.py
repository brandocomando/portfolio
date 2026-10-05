"""Health Check & Readiness Endpoints for Cloud Run & Kubernetes."""

import time
import datetime
from fastapi import APIRouter, Response, status
from backend.app.core.config import settings
from backend.app.services.retrieval_service import retrieval_service

router = APIRouter(tags=["health"])

START_TIME = time.time()


@router.get("/healthz", summary="Liveness Probe")
async def healthz():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "env": settings.ENV,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": int(time.time() - START_TIME)
    }


@router.get("/readyz", summary="Readiness Probe")
async def readyz(response: Response):
    try:
        # Check if in-memory retriever is loaded with chunks
        num_chunks = len(retrieval_service.retriever.chunks_map)
        if num_chunks == 0:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "unready", "reason": "No chunks loaded in vector index"}

        return {
            "status": "ready",
            "index_version": retrieval_service.retriever.version,
            "chunks_loaded": num_chunks
        }
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "error": str(e)}


@router.get("/metrics", summary="Basic Metrics")
async def metrics():
    return {
        "uptime_seconds": int(time.time() - START_TIME),
        "total_chunks_indexed": len(retrieval_service.retriever.chunks_map),
        "embedding_dim": retrieval_service.retriever.dim,
        "rate_limit_anon": settings.ANON_DAILY_LIMIT,
        "rate_limit_auth": settings.AUTH_DAILY_LIMIT
    }
