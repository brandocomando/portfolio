"""Lead and Quota API endpoints."""

from fastapi import APIRouter, Depends
from backend.app.core.security import UserIdentity, get_current_user_optional
from backend.app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/quota", summary="Get User Rate Limit Quota")
async def get_user_quota(user: UserIdentity = Depends(get_current_user_optional)):
    """Returns current query quota and authentication tier for the client."""
    # Check without consuming a token
    status = rate_limiter.get_quota_status(user)
    return {
        "authenticated": user.is_authenticated,
        "tier": status.tier,
        "limit": status.limit,
        "remaining": status.remaining,
        "reset_seconds": status.reset_seconds,
        "user_email": user.email,
        "user_name": user.name
    }
