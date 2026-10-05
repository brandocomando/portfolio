"""Integration tests for Health and Chat Endpoints."""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


def extract_streamed_text(sse_body: str) -> str:
    tokens = []
    for line in sse_body.splitlines():
        if line.startswith("data: ") and '"token"' in line:
            try:
                data = json.loads(line[6:])
                tokens.append(data.get("token", ""))
            except Exception:
                pass
    return "".join(tokens)


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

        streamed = extract_streamed_text(body)
        assert "Kubernetes" in streamed
        assert "Amazon EKS" in streamed
        # Ensure it does NOT dump raw internal tags
        assert "[TECHNICAL" not in streamed
        assert "[CAREER" not in streamed
        assert "GitHub Stars: 0" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_conversational_ping():
    """Verify that 'test' returns conversational dialogue without dumping document sources."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "test"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        body = resp.text
        assert "event: sources" in body
        assert '"sources": []' in body

        streamed = extract_streamed_text(body)
        assert "Systems are up and running" in streamed
        assert "[TECHNICAL SKILLS" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_conversational_greeting():
    """Verify that 'hello' greets warmly without attaching document hits."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "hello"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        body = resp.text
        assert '"sources": []' in body

        streamed = extract_streamed_text(body)
        assert "Hey! I'm Brandon Foster's AI assistant" in streamed


@pytest.mark.asyncio
async def test_chat_stream_conversational_python():
    """Verify that asking about Python directly answers conversationally."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "Does Brandon know Python?"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        body = resp.text

        streamed = extract_streamed_text(body)
        assert "Yes, Brandon works with Python regularly" in streamed
        assert "FastAPI" in streamed
