"""Integration tests for Health and Chat Endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Liveness
        resp = await ac.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # Readiness
        resp = await ac.get("/readyz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"
        assert resp.json()["chunks_loaded"] > 0

        # Metrics
        resp = await ac.get("/metrics")
        assert resp.status_code == 200
        assert resp.json()["total_chunks_indexed"] > 0


@pytest.mark.asyncio
async def test_chat_stream_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "What is Brandon's experience with Kubernetes and EKS?"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        body = resp.text
        assert "event: sources" in body
        assert "event: token" in body
        assert "event: done" in body
