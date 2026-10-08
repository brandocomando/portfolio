import time
import hashlib
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel
from fastapi import HTTPException, status, Depends

from backend.app.core.config import settings
from backend.app.core.security import UserIdentity, get_current_user_optional

logger = logging.getLogger("portfolio.rate_limiter")


class RateLimitStatus(BaseModel):
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    tier: str


class InMemoryRateLimiter:
    """Sliding-window rate limiter with Firestore persistence and in-memory cache/fallback."""

    def __init__(self):
        # Maps bucket_key -> List of epoch timestamps
        self._buckets: Dict[str, List[float]] = {}
        self._last_cleanup: float = time.time()
        self._firestore_client = None
        self._firestore_initialized = False

    def _get_firestore_client(self):
        if not self._firestore_initialized:
            try:
                from google.cloud import firestore
                self._firestore_client = firestore.Client(project=settings.GCP_PROJECT_ID)
                self._firestore_initialized = True
            except Exception as e:
                logger.warning(f"Firestore rate-limiter initialization skipped or failed: {e}")
                self._firestore_initialized = True
                self._firestore_client = None
        return self._firestore_client

    def _firestore_doc_id(self, key: str) -> str:
        """Ensures bucket key is a safe, valid Firestore document ID."""
        # Clean safe characters: replace slashes or disallowed characters
        safe_key = key.replace("/", "_")
        if len(safe_key) > 100:
            return hashlib.sha256(key.encode("utf-8")).hexdigest()
        return safe_key

    def _load_timestamps(self, key: str, now: float, window: float) -> List[float]:
        """Loads active timestamps from memory, falling back to Firestore if not cached locally."""
        if key in self._buckets:
            return [ts for ts in self._buckets[key] if now - ts < window]

        # Not in memory: query Firestore
        client = self._get_firestore_client()
        if client:
            try:
                doc_id = self._firestore_doc_id(key)
                doc_ref = client.collection(settings.FIRESTORE_COLLECTION_QUOTA).document(doc_id)
                doc = doc_ref.get()
                if doc.exists:
                    data = doc.to_dict() or {}
                    ts_list = data.get("timestamps", [])
                    if isinstance(ts_list, list):
                        valid = [float(ts) for ts in ts_list if isinstance(ts, (int, float)) and now - float(ts) < window]
                        self._buckets[key] = valid
                        return valid
            except Exception as e:
                logger.warning(f"Failed to read rate-limit quota from Firestore for key '{key}': {e}")

        return []

    def _persist_timestamps(self, key: str, timestamps: List[float], user: UserIdentity, tier: str, limit: int):
        """Persists updated timestamps to Firestore (best-effort, non-blocking to client)."""
        client = self._get_firestore_client()
        if not client:
            return

        try:
            doc_id = self._firestore_doc_id(key)
            doc_ref = client.collection(settings.FIRESTORE_COLLECTION_QUOTA).document(doc_id)
            doc_ref.set({
                "bucket_key": key,
                "tier": tier,
                "limit": limit,
                "is_authenticated": user.is_authenticated,
                "uid": user.uid,
                "client_ip": user.client_ip,
                "timestamps": timestamps,
                "count": len(timestamps),
                "last_updated": time.time(),
            }, merge=True)
        except Exception as e:
            logger.warning(f"Failed to persist rate-limit quota to Firestore for key '{key}': {e}")

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

        active_timestamps = self._load_timestamps(key, now, window)
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

        # Persist across container restarts
        self._persist_timestamps(key, active_timestamps, user, tier, limit)

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

