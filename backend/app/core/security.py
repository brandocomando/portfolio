"""Security & Authentication Module.

Cryptographically verifies Firebase Authentication ID tokens (Google/GitHub/Email OAuth)
and yields strongly typed User context.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import Request, Header, HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from backend.app.core.config import settings

google_request_adapter = google_requests.Request()


class UserIdentity(BaseModel):
    is_authenticated: bool
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: Optional[str] = None
    client_ip: str


def get_client_ip(request: Request) -> str:
    """Extracts client IP, respecting trusted edge and proxy headers."""
    for header in ["fastly-client-ip", "cf-connecting-ip", "x-real-ip", "x-client-ip"]:
        val = request.headers.get(header)
        if val:
            return val.strip()

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Take the leftmost client IP
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


async def get_current_user_optional(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> UserIdentity:
    """Extracts user identity from Firebase Bearer token if present, otherwise returns Anonymous."""
    client_ip = get_client_ip(request)
    session_id = request.headers.get("x-session-id")
    anon_key = f"{client_ip}:{session_id.strip()}" if session_id and session_id.strip() else client_ip

    if not authorization or not authorization.startswith("Bearer "):
        return UserIdentity(
            is_authenticated=False,
            uid=f"anon:{anon_key}",
            client_ip=client_ip
        )

    token = authorization.split("Bearer ", 1)[1].strip()

    # Handle local dev/testing token bypass
    if settings.DEBUG and token.startswith("dev-test-token-"):
        uid = token.replace("dev-test-token-", "")
        return UserIdentity(
            is_authenticated=True,
            uid=uid,
            email=f"{uid}@example.com",
            name=f"Dev User {uid.capitalize()}",
            provider="google.com",
            client_ip=client_ip
        )

    try:
        # Cryptographically verify Firebase JWT against Google's public key certs
        claims = id_token.verify_firebase_token(
            token,
            google_request_adapter,
            audience=settings.FIREBASE_PROJECT_ID
        )

        uid = claims.get("sub") or claims.get("user_id")
        email = claims.get("email")
        name = claims.get("name")
        picture = claims.get("picture")
        firebase_info = claims.get("firebase", {})
        provider = firebase_info.get("sign_in_provider", "unknown")

        return UserIdentity(
            is_authenticated=True,
            uid=uid,
            email=email,
            name=name,
            picture=picture,
            provider=provider,
            client_ip=client_ip
        )
    except Exception as e:
        # If an invalid token was provided, treat as anonymous or reject
        return UserIdentity(
            is_authenticated=False,
            uid=f"anon:{client_ip}",
            client_ip=client_ip
        )
