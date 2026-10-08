"""Unit tests for Multi-Tier Token Bucket Rate Limiter."""

import pytest
from fastapi import HTTPException
from backend.app.core.security import UserIdentity
from backend.app.core.rate_limiter import InMemoryRateLimiter


from backend.app.core.config import settings


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
        assert status.remaining == settings.ANON_DAILY_LIMIT
        assert status.limit == settings.ANON_DAILY_LIMIT


def test_anonymous_rate_limit_enforcement():
    limiter = InMemoryRateLimiter()
    anon_user = UserIdentity(
        is_authenticated=False,
        uid="anon:192.168.1.50",
        client_ip="192.168.1.50"
    )

    limit = settings.ANON_DAILY_LIMIT
    for i in range(limit):
        status = limiter.check_limit(anon_user, consume=True)
        assert status.allowed is True
        assert status.tier == "anonymous"
        assert status.remaining == (limit - 1) - i

    # Next call must raise HTTPException 429
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

    limit = settings.AUTH_DAILY_LIMIT
    for i in range(limit):
        status = limiter.check_limit(auth_user, consume=True)
        assert status.allowed is True
        assert status.tier == "authenticated"

    assert status.remaining == 0

    # Next call raises 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_limit(auth_user, consume=True)
    assert exc_info.value.status_code == 429


def test_rate_limit_exception_message_contains_dynamic_limit(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DAILY_LIMIT", 50)
    monkeypatch.setattr(settings, "ANON_DAILY_LIMIT", 5)

    limiter = InMemoryRateLimiter()
    anon_user = UserIdentity(
        is_authenticated=False,
        uid="anon:10.0.0.1",
        client_ip="10.0.0.1"
    )

    for _ in range(5):
        limiter.check_limit(anon_user, consume=True)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check_limit(anon_user, consume=True)

    msg = exc_info.value.detail["message"]
    assert "50 daily questions" in msg
    assert "limit of 5 questions" in msg


@pytest.mark.asyncio
async def test_get_user_quota_returns_auth_and_anon_limits():
    from fastapi import BackgroundTasks
    from backend.app.api.v1.leads import get_user_quota

    anon_user = UserIdentity(
        is_authenticated=False,
        uid="anon:10.0.0.2",
        client_ip="10.0.0.2"
    )
    bg = BackgroundTasks()
    result = await get_user_quota(background_tasks=bg, user=anon_user)
    assert result["authenticated"] is False
    assert result["auth_limit"] == settings.AUTH_DAILY_LIMIT
    assert result["anon_limit"] == settings.ANON_DAILY_LIMIT
    assert result["limit"] == 5


@pytest.mark.asyncio
async def test_get_user_quota_authenticated_schedules_login_record():
    from fastapi import BackgroundTasks
    from backend.app.api.v1.leads import get_user_quota

    auth_user = UserIdentity(
        is_authenticated=True,
        uid="usr_github_999",
        email="recruiter@tech.com",
        name="Senior Recruiter",
        provider="github",
        client_ip="10.0.0.3"
    )
    bg = BackgroundTasks()
    result = await get_user_quota(background_tasks=bg, user=auth_user)
    assert result["authenticated"] is True
    assert result["auth_limit"] == 10
    assert result["limit"] == 10
    assert len(bg.tasks) == 1
