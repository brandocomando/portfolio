import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, BackgroundTasks

from backend.app.core.config import settings
from backend.app.core.security import UserIdentity, get_current_user_optional
from backend.app.core.rate_limiter import rate_limiter
from backend.app.services.firestore_service import firestore_service

router = APIRouter(prefix="/leads", tags=["leads"])


class ContactSubmissionRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    question: str = Field(..., min_length=3, max_length=3000)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address format")
        return v


@router.get("/quota", summary="Get User Rate Limit Quota")
async def get_user_quota(
    background_tasks: BackgroundTasks,
    user: UserIdentity = Depends(get_current_user_optional)
):
    """Returns current query quota and authentication tier for the client."""
    if user.is_authenticated:
        background_tasks.add_task(firestore_service.record_user_login, user)

    # Check without consuming a token
    status = rate_limiter.get_quota_status(user)
    return {
        "authenticated": user.is_authenticated,
        "tier": status.tier,
        "limit": status.limit,
        "remaining": status.remaining,
        "reset_seconds": status.reset_seconds,
        "user_email": user.email,
        "user_name": user.name,
        "auth_limit": settings.AUTH_DAILY_LIMIT,
        "anon_limit": settings.ANON_DAILY_LIMIT,
    }


@router.post("/contact", summary="Submit Visitor Question or Inquiry")
async def submit_contact_form(
    submission: ContactSubmissionRequest,
    user: UserIdentity = Depends(get_current_user_optional)
):
    """Stores the visitor's question in Firestore and forwards an alert to Brandon."""
    await firestore_service.record_contact_message(
        email=submission.email,
        question=submission.question,
        name=submission.name,
        client_ip=user.client_ip
    )
    return {
        "status": "success",
        "message": "Thank you! Your question has been forwarded directly to Brandon."
    }
