"""Multi-Tier Token Bucket Rate Limiter.

Protects LLM API budgets by enforcing strict daily query limits:
- Anonymous Tier: 5 queries / 24 hours (keyed by Client IP)
- Authenticated Tier: 30 queries / 24 hours (keyed by Firebase UID)
"""

import time
from typing import Dict, List, Optional
from pydantic import BaseModel
from fastapi import HTTPException, status, Depends

from backend.app.core.config import settings
from backend.app.core.security import UserIdentity, get_current_user_optional


class RateLimitStatus(BaseModel):
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    tier: str


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter with periodic cleanup."""

    def __init__(self):
        # Maps bucket_key -> List of epoch timestamps
        self._buckets: Dict[str, List[float]] = {}
        self._last_cleanup: float = time.time()

    def _cleanup_old_entries(self, now: float, window: float):
        """Purges buckets with no active entries in the current window."""
        if now - self._last_cleanup < 300:  # Run cleanup at most once every 5 minutes
            return
        keys_to_delete = []
        for key, timestamps in self._buckets.items():
            valid = [ts for ts in timestamps if now - ts < window]
            if not valid:
                keys_to_delete.append(key)
            else:
                self._buckets[key] = valid
        for key in keys_to_delete:
            del self._buckets[key]
        self._last_cleanup = now

    def check_limit(self, user: UserIdentity, consume: bool = True) -> RateLimitStatus:
        now = time.time()
        window = float(settings.RATE_LIMIT_WINDOW_SECONDS)

        self._cleanup_old_entries(now, window)

        if user.is_authenticated:
            key = f"auth:{user.uid}"
            limit = settings.AUTH_DAILY_LIMIT
            tier = "authenticated"
        else:
            key = user.uid if user.uid.startswith("anon:") else f"anon:{user.client_ip}"
            limit = settings.ANON_DAILY_LIMIT
            tier = "anonymous"

        timestamps = self._buckets.get(key, [])
        # Keep only timestamps within the rolling window
        active_timestamps = [ts for ts in timestamps if now - ts < window]
        self._buckets[key] = active_timestamps

        remaining = max(0, limit - len(active_timestamps))
        reset_seconds = int(window)
        if active_timestamps:
            oldest = active_timestamps[0]
            reset_seconds = int(max(1, window - (now - oldest)))

        # Read-only check: never consume tokens and never raise 429
        if not consume:
            return RateLimitStatus(
                allowed=remaining > 0,
                limit=limit,
                remaining=remaining,
                reset_seconds=reset_seconds,
                tier=tier
            )

        if len(active_timestamps) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "tier": tier,
                    "limit": limit,
                    "remaining": 0,
                    "reset_seconds": reset_seconds,
                    "requires_auth": not user.is_authenticated,
                    "message": (
                        f"You've reached your daily limit of {limit} questions as an anonymous visitor. "
                        f"Sign in with Google or GitHub to unlock {settings.AUTH_DAILY_LIMIT} daily questions and connect directly with Brandon!"
                        if not user.is_authenticated
                        else f"You've reached your authenticated limit of {limit} questions per day. Quota resets in {reset_seconds // 3600}h {(reset_seconds % 3600) // 60}m."
                    )
                }
            )

        # Record this request
        active_timestamps.append(now)
        self._buckets[key] = active_timestamps
        remaining = max(0, limit - len(active_timestamps))

        return RateLimitStatus(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_seconds=reset_seconds,
            tier=tier
        )

    def get_quota_status(self, user: UserIdentity) -> RateLimitStatus:
        """Inspects current quota without consuming any tokens or raising 429."""
        return self.check_limit(user, consume=False)


rate_limiter = InMemoryRateLimiter()


def rate_limit_gate(
    user: UserIdentity = Depends(get_current_user_optional)
) -> RateLimitStatus:
    return rate_limiter.check_limit(user, consume=True)
