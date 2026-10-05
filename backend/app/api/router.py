"""Central API router grouping all v1 routes."""

from fastapi import APIRouter
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.leads import router as leads_router
from backend.app.api.v1.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(chat_router)
api_v1_router.include_router(leads_router)
api_v1_router.include_router(health_router)
