"""Unit tests for Multi-Tier Token Bucket Rate Limiter."""

import pytest
from fastapi import HTTPException
from backend.app.core.security import UserIdentity
from backend.app.core.rate_limiter import InMemoryRateLimiter


def test_read_only_quota_check_does_not_consume():
    limiter = InMemoryRateLimiter()
    anon_user = UserIdentity(
        is_authenticated=False,
        uid="anon:192.168.1.50:session-abc",
        client_ip="192.168.1.50"
    )

    # Calling get_quota_status 50 times should NEVER consume any quota
    for _ in range(50):
        status = limiter.get_quota_status(anon_user)
        assert status.allowed is True
        assert status.tier == "anonymous"
        assert status.remaining == 10
        assert status.limit == 10


def test_anonymous_rate_limit_enforcement():
    limiter = InMemoryRateLimiter()
    anon_user = UserIdentity(
        is_authenticated=False,
        uid="anon:192.168.1.50",
        client_ip="192.168.1.50"
    )

    # 10 calls should succeed (ANON_DAILY_LIMIT = 10)
    for i in range(10):
        status = limiter.check_limit(anon_user, consume=True)
        assert status.allowed is True
        assert status.tier == "anonymous"
        assert status.remaining == 9 - i

    # 11th call must raise HTTPException 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_limit(anon_user, consume=True)

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
        status = limiter.check_limit(auth_user, consume=True)
        assert status.allowed is True
        assert status.tier == "authenticated"

    assert status.remaining == 15
