"""Tests for Client Verification Middleware and CORS Security."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_public_endpoints_bypass_client_verification():
    """Ensure monitoring and health endpoints never require verification header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for path in ["/healthz", "/readyz", "/metrics", "/api/v1/healthz"]:
            resp = await ac.get(path)
            assert resp.status_code == 200, f"Expected 200 for {path}, got {resp.status_code}"


@pytest.mark.asyncio
async def test_protected_endpoint_allowed_with_valid_header(monkeypatch):
    """Ensure requests with the verified client header succeed."""
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "CLIENT_VERIFICATION_ENABLED", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/leads/quota",
            headers={"x-portfolio-client": "portfolio-client-v1"}
        )
        assert resp.status_code == 200
        assert "tier" in resp.json()


@pytest.mark.asyncio
async def test_protected_endpoint_blocked_in_production_without_header(monkeypatch):
    """Ensure unauthorized direct requests are blocked in production."""
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "CLIENT_VERIFICATION_ENABLED", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Missing header
        resp = await ac.get(
            "/api/v1/leads/quota",
            headers={"host": "api.cloudrun.app"}
        )
        assert resp.status_code == 403
        assert "Direct API access forbidden" in resp.json()["detail"]

        # Invalid header
        resp2 = await ac.get(
            "/api/v1/leads/quota",
            headers={
                "host": "api.cloudrun.app",
                "x-portfolio-client": "bad-token"
            }
        )
        assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_allows_local_dev_fallback(monkeypatch):
    """Ensure local developers on localhost/127.0.0.1 aren't blocked in development mode."""
    monkeypatch.setattr(settings, "ENV", "development")
    monkeypatch.setattr(settings, "DEBUG", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8080") as ac:
        resp = await ac.get(
            "/api/v1/leads/quota",
            headers={"host": "localhost:8080"}
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_cors_preflight_and_allowed_origins():
    """Ensure CORS preflight permits custom domain and rejects unlisted origins."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Allowed apex domain
        resp_allowed = await ac.options(
            "/api/v1/leads/quota",
            headers={
                "Origin": "https://brandonfoster.dev",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-portfolio-client,x-session-id"
            }
        )
        assert resp_allowed.status_code == 200
        assert resp_allowed.headers.get("access-control-allow-origin") == "https://brandonfoster.dev"

        # Allowed www subdomain
        resp_www = await ac.options(
            "/api/v1/leads/quota",
            headers={
                "Origin": "https://www.brandonfoster.dev",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert resp_www.status_code == 200
        assert resp_www.headers.get("access-control-allow-origin") == "https://www.brandonfoster.dev"

        # Disallowed third-party origin
        resp_disallowed = await ac.options(
            "/api/v1/leads/quota",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert resp_disallowed.headers.get("access-control-allow-origin") is None
