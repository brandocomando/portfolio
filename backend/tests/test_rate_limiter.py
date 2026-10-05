"""Unit tests for Multi-Tier Token Bucket Rate Limiter."""

import pytest
from fastapi import HTTPException
from backend.app.core.security import UserIdentity
from backend.app.core.rate_limiter import InMemoryRateLimiter


def test_anonymous_rate_limit_enforcement():
    limiter = InMemoryRateLimiter()
    anon_user = UserIdentity(
        is_authenticated=False,
        uid="anon:192.168.1.50",
        client_ip="192.168.1.50"
    )

    # First 5 calls should succeed
    for i in range(5):
        status = limiter.check_limit(anon_user)
        assert status.allowed is True
        assert status.tier == "anonymous"
        assert status.remaining == 4 - i

    # 6th call must raise HTTPException 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_limit(anon_user)

    assert exc_info.value.status_code == 429
    detail = exc_info.value.detail
    assert detail["error"] == "rate_limit_exceeded"
    assert detail["tier"] == "anonymous"
    assert detail["requires_auth"] is True


def test_authenticated_rate_limit_allowance():
    limiter = InMemoryRateLimiter()
    auth_user = UserIdentity(
        is_authenticated=True,
        uid="usr_google_12345",
        email="recruiter@example.com",
        client_ip="192.168.1.50"
    )

    # Authenticated user should have up to 30 calls
    for i in range(15):
        status = limiter.check_limit(auth_user)
        assert status.allowed is True
        assert status.tier == "authenticated"

    assert status.remaining == 15
